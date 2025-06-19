
import os
import json
import re
from dotenv import load_dotenv
from google.genai import types

from Utils.SkillGraph import SkillGraph

load_dotenv()

class BaseSchemaManager:
    def __init__(self):
        self.showLoadedTools = os.getenv('SHOW_LOADED_TOOLS', 'False') == 'True'
        self.graph = SkillSkillGraph()
        self._toolFunctions = None
        self._toolSchemas = None
        self.printToolsSchema()

    def loadTools(self):
        if self._toolFunctions is None:
            self._toolFunctions = self.graph.getTools()
        return self._toolFunctions

    def callFunction(self, *args, **kwargs):
        return self.graph.executeTool(*args, **kwargs)

    def extractJson(self, *args, **kwargs):
        return self.graph.extractJson(*args, **kwargs)

    def buildToolSchema(self, func):
        raise NotImplementedError("Subclasses must implement buildToolSchema.")

    def getToolFunctions(self):
        return self.loadTools()

    def getToolSchemas(self):
        if self._toolSchemas is None:
            toolFunctions = self.getToolFunctions()
            self._toolSchemas = [self.buildToolSchema(f) for f in toolFunctions.values()]
        return self._toolSchemas

    

class JsonSchemaManager(BaseSchemaManager):

    def buildToolSchema(self, func, schemaType="chat_completions"):
        return self.graph.getJsonSchema(func, schemaType)

    def handleFormat(self, role: str, content: str):
        return self.graph.handleJsonFormat(role, content)

    def printToolsSchema(self):
        if self.showLoadedTools:
            tools = self.getToolSchemas()
            print(f"Discovered tools: {list(self.getToolFunctions().keys())}")
            schemaJson = json.dumps(tools, indent=2)
            schemaJson = re.sub(
                r'("description": ")(.*?)(\")',
                lambda m: m.group(1) + m.group(2).replace('\\n', '\n\t\t') + m.group(3),
                schemaJson,
                flags=re.DOTALL
            )
            print(f"Tools schema: {schemaJson}")



class TypedSchemaManager(BaseSchemaManager):

    def buildToolSchema(self, func):
        return self.graph.getTypedSchema(func)

    def buildTools(self):
        toolFunctions = self.loadTools()
        functionDeclarations = [self.buildToolSchema(f) for f in toolFunctions.values()]
        tools = [types.Tool(function_declarations=functionDeclarations)]
        self._toolSchemas = tools
        return tools

    def getToolSchemas(self):
        if self._toolSchemas is None:
            return self.buildTools()
        return self._toolSchemas

    def handleFormat(self, role: str, content: str):
        return self.graph.handleTypedFormat(role, content)

    def serializeSchema(self, schema, visited=None):
        if visited is None:
            visited = set()
        if id(schema) in visited:
            return f"<recursion id={id(schema)}>"
        visited.add(id(schema))
        schemaDict = {}
        if hasattr(schema, 'type'):
            schemaDict['type'] = getattr(schema, 'type', None)
        if hasattr(schema, 'description'):
            desc = getattr(schema, 'description', None)
            if desc:
                schemaDict['description'] = desc
        if hasattr(schema, 'enum'):
            enum = getattr(schema, 'enum', None)
            if enum:
                schemaDict['enum'] = enum
        if hasattr(schema, 'properties') and schema.properties:
            schemaDict['properties'] = {k: self.serializeSchema(v, visited) for k, v in schema.properties.items()}
        if hasattr(schema, 'items'):
            items = getattr(schema, 'items', None)
            if items:
                schemaDict['items'] = self.serializeSchema(items, visited)
        return schemaDict

    def printToolsSchema(self):
        if self.showLoadedTools:
            toolsDict = self.getToolFunctions()
            print(f"Discovered tools: {list(toolsDict.keys())}")
            toolsSchema = self.getToolSchemas()
            functionDeclarations = toolsSchema[0].function_declarations
            outputSchemas = []
            for fn in functionDeclarations:
                schemaObj = {
                    "type": "function",
                    "function": {
                        "name": fn.name,
                        "description": fn.description,
                        "parameters": self.serializeSchema(fn.parameters),
                    }
                }
                outputSchemas.append(schemaObj)
            schemaJson = json.dumps(outputSchemas, indent=2)
            schemaJson = re.sub(
                r'("description": ")(.*?)(\")',
                lambda m: m.group(1) + m.group(2).replace('\\n', '\n\t\t') + m.group(3),
                schemaJson,
                flags=re.DOTALL
            )
            print(f"Tools schema: {schemaJson}")
