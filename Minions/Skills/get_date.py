
from datetime import datetime
from SkillLink import ArgumentParser

argParser = ArgumentParser()

def get_current_date():
    """
    Description: "Get the current date in DD-MM-YYYY format."
    Additional Information: "This function returns the current date formatted as day-month-year."
    """
    #print("Fetching the current date")
    
    argParser.printArgs(__name__, locals())
    return datetime.now().strftime('%d-%B-%Y')