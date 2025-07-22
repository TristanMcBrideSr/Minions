
import json
import re
import inspect
import os
import threading
import logging
from dotenv import load_dotenv
from pathlib import Path

from SkillLink import SkillLink # Dont for get to pip install SkillLink

load_dotenv()

logger = logging.getLogger(__name__)


class SkillGraph:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SkillGraph, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, 'initialized', False):
            return
        self._initComponents()
        self.initialized = True

    def _initComponents(self):
        self.skillLink         = SkillLink()
        self.printCapabilities = os.getenv('SHOW_CAPABILITIES', 'False') == 'True'
        self.printMetaData     = os.getenv('SHOW_METADATA', 'False') == 'True'
        self.loadAllComponents()

    def getDir(self, *paths):
        return self.skillLink.getDir(*paths)

    def loadAllComponents(self):
        """
        Load all components from the specified directories.
        This method loads skills and tools from the 'Skills' directory.
        """
        self.minionSkills = []

        self.skillLink.loadComponents(
            paths=[
                ['Skills'],
            ],
            components=[
                self.minionSkills,
            ],
            reloadable=[
                False
            ]
        )

    def getMinionActions(self):
        """
        Get self actions based on the skills available.
        This method combines dynamic, static, and restricted self skills.
        """
        skills = (
            self.minionSkills
        )
        return self.skillLink.getComponents(skills)

    def reloadSkills(self):
        """
        Reload all skills and print any new skills added.
        """
        original = self.getMetaData()
        self.skillLink.reloadSkills()
        new = self.getMetaData()
        for skill in new:
            if skill not in original:
                print(f"I've added the new skill {skill['className']} That {skill['description']}.\n")

    def getMetaData(self):
        """Get metadata for all skills."""
        metaData = (
                self.minionSkills
        )
        return self.skillLink.getMetaData(metaData, self.printMetaData)

    # ----- Skills -----
    def getMinionCapabilities(self):
        """
        Get the capabilities of the agent based on its skills.
        This method retrieves the capabilities of the agent's skills and returns them in a structured format.
        """
        description = False
        capabitites = (
            self.minionSkills
        )
        return self.skillLink.getCapabilities(capabitites, self.printCapabilities, description)

    def checkActions(self, action: str) -> str:
        """
        Check if the given action is valid based on the agent's skills.
        Returns a string indicating whether the action is valid or not.
        """
        return self.skillLink.actionParser.checkActions(action)

    def getActions(self, action: str) -> list:
        """
        Get a list of actions based on the given action string.
        This method uses the skills manager's action parser to retrieve actions that match the given string.
        If the action is not found, it returns an empty list.
        """
        return self.skillLink.actionParser.getActions(action)

    def executeAction(self, actions, action):
        """
        Execute a single action based on the provided actions and action string.
        You must create your own for loop if you want to execute multiple actions.
        """
        return self.skillLink.actionParser.executeAction(actions, action)

    def executeActions(self, actions, action):
        """
        Execute both single and multiple actions based on the provided actions and action string.
        The for loop is handled internally, so you can pass a single action or a list of actions.
        """
        return self.skillLink.actionParser.executeActions(actions, action)

    def skillInstructions(self):
        """
        Get skill instructions for the agent based on its capabilities.
        """
        return self.skillLink.skillInstructions(self.getMinionCapabilities())

    def isStructured(self, *args):
        """
        Check if any of the arguments is a list of dictionaries.
        This indicates structured input (multi-message format).
        """
        return self.skillLink.isStructured(*args)

    def handleTypedFormat(self, role: str = "user", content: str = ""):
        """
        Format content for Google GenAI APIs.
        """
        return self.skillLink.handleTypedFormat(role, content)

    def handleJsonFormat(self, role: str = "user", content: str = ""):
        """
        Format content for OpenAI APIs and similar JSON-based APIs.
        """
        return self.skillLink.handleJsonFormat(role, content)

    def buildGoogleSafetySettings(self, harassment="BLOCK_NONE", hateSpeech="BLOCK_NONE", sexuallyExplicit="BLOCK_NONE", dangerousContent="BLOCK_NONE"):
        """
        Construct a list of Google GenAI SafetySetting objects.
        """
        return self.skillLink.buildGoogleSafetySettings(harassment, hateSpeech, sexuallyExplicit, dangerousContent)

