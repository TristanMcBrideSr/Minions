
from datetime import datetime
from SkillsManager import ArgumentParser

argParser = ArgumentParser()

def get_current_time():
    """
    Description: "Get the current time in 12-hour format with am/pm"
    """
    argParser.printArgs(__name__, locals())
    return datetime.now().strftime("%I:%M%p").lstrip("0").lower()
