from openai import OpenAI
from google import genai
from google.genai import types
from .settings import SettingsManager
from ..utils.logger import setup_logger
import os
import base64
import json

logger = setup_logger("llm")

class LLMService:
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.reload_settings()

    def reload_settings(self):
        settings = self.settings_manager.load()
        self.provider = settings.get("provider", "lm_studio")
        
        if self.provider == "lm_studio":
            self.base_url = settings.get("lm_studio_url", "http://localhost:1234/v1")
            self.model = settings.get("lm_studio_model", "qwen/qwen3-vl-8b")
            self.client = OpenAI(base_url=self.base_url, api_key="lm-studio")
            logger.info(f"LLM: Switched to LM Studio ({self.model})")
            
        elif self.provider == "gemini":
            self.api_key = settings.get("gemini_api_key", "")
            self.model = settings.get("gemini_model", "gemini-1.5-flash-latest")
            if self.api_key:
                self.gemini_client = genai.Client(api_key=self.api_key)
                logger.info(f"LLM: Switched to Gemini ({self.model})")
            else:
                logger.warning("LLM: Gemini selected but no API Key found.")
                self.gemini_client = None

    def chat(self, messages: list, tools: list = None):
        # Reload settings on each chat to catch dynamic updates
        self.reload_settings()
        
        if self.provider == "lm_studio":
            return self._chat_openai(messages, tools)
        elif self.provider == "gemini":
            return self._chat_gemini(messages, tools)
        return {"error": "Invalid Provider"}

    def _chat_openai(self, messages: list, tools: list = None):
        if not self.client:
            return {"error": "No Client"}

        logger.info(f"Sending request to LM Studio ({self.model})...")
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1000
            }
            if tools:
                kwargs["tools"] = tools

            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message
        except Exception as e:
            logger.error(f"LLM Error (OpenAI): {e}")
            return None

    def _convert_tools_to_gemini(self, tools: list):
        """
        Converts OpenAI-style tool definitions to Gemini types.Tool.
        """
        if not tools:
            return None
            
        function_declarations = []
        for tool in tools:
            if tool.get("type") != "function":
                continue
                
            fn = tool.get("function", {})
            name = fn.get("name")
            description = fn.get("description")
            parameters = fn.get("parameters", {})
            
            # Map parameters to types.Schema
            properties = {}
            required = parameters.get("required", [])
            
            for param_name, param_info in parameters.get("properties", {}).items():
                param_type = param_info.get("type", "STRING").upper()
                
                if param_type == "STRING":
                    schema_type = types.Type.STRING
                elif param_type == "INTEGER":
                    schema_type = types.Type.INTEGER
                elif param_type == "NUMBER":
                    schema_type = types.Type.NUMBER
                elif param_type == "BOOLEAN":
                    schema_type = types.Type.BOOLEAN
                else:
                    schema_type = types.Type.STRING 

                properties[param_name] = types.Schema(
                    type=schema_type,
                    description=param_info.get("description")
                )
            
            # Gemini Schema
            function_declarations.append(types.FunctionDeclaration(
                name=name,
                description=description,
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties=properties,
                    required=required
                )
            ))
            
        if not function_declarations:
            return None
            
        return [types.Tool(function_declarations=function_declarations)]

    def _chat_gemini(self, messages: list, tools: list = None):
        if not self.gemini_client:
            return {"error": "Gemini not configured"}

        logger.info(f"Sending request to Gemini ({self.model})...")
        try:
            # Prepare contents
            contents = []
            system_instruction = "You are a helpful Browser Agent."
            
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                elif msg["role"] == "user":
                    parts = []
                    if isinstance(msg["content"], str):
                        parts.append(types.Part.from_text(text=msg["content"]))
                    else:
                        for part in msg["content"]:
                            if part["type"] == "text":
                                parts.append(types.Part.from_text(text=part["text"]))
                            elif part["type"] == "image_url":
                                url = part["image_url"]["url"]
                                if "base64," in url:
                                    b64_str = url.split("base64,")[1]
                                    img_bytes = base64.b64decode(b64_str)
                                    parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
                    
                    contents.append(types.Content(role="user", parts=parts))
                    
                elif msg["role"] == "assistant":
                     # Handle assistant text
                    parts = []
                    if msg.get("content"):
                         parts.append(types.Part.from_text(text=msg["content"]))
                    
                    if parts:
                        contents.append(types.Content(role="model", parts=parts))

            # Prepare Methods & Config
            gemini_tools = self._convert_tools_to_gemini(tools)
            logger.info(f"DEBUG: Gemini Tools: {gemini_tools}")
            
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                tools=gemini_tools, 
            )
            
            response = self.gemini_client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
            
            # Map Response
            content = None
            tool_calls = []

            # Helper Classes for mocking OpenAI structure locally
            class CustomToolCall:
                def __init__(self, name, arguments):
                    self.id = "call_" + base64.b64encode(os.urandom(4)).decode("utf-8").replace("=","")
                    self.type = "function"
                    self.function = self.Function(name, arguments)
                
                class Function:
                    def __init__(self, name, arguments):
                        self.name = name
                        self.arguments = arguments

            class MockMessage:
                def __init__(self, content, tool_calls):
                    self.content = content
                    self.tool_calls = tool_calls

            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if part.text:
                        content = part.text
                    elif part.function_call:
                        # Parse args dict directly as it returns Dict, OpenAI needs JSON string
                        # The SDK returns struct for args.
                        args_dict = {}
                        if part.function_call.args:
                             # part.function_call.args is a Map (behaves like dict)
                             # We can iterate or cast.
                             args_dict = dict(part.function_call.args)
                        
                        tool_calls.append(CustomToolCall(
                            name=part.function_call.name,
                            arguments=json.dumps(args_dict)
                        ))
            
            return MockMessage(content, tool_calls)
            
        except Exception as e:
            logger.error(f"LLM Error (Gemini): {e}")
            return {"error": str(e)}
