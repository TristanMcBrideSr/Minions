import random
import os
from dotenv import load_dotenv

from Utils.Names import MAIN_MINIONS, SUB_MINIONS
from Utils.SkillGraph import SkillGraph

from openai import OpenAI
from google import genai
from google.genai import types

load_dotenv()
gptClient = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
genClient = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

graph = SkillGraph()
skillInstructions = graph.skillInstructions()

class MinionTool:
    def __init__(self):
        self.provider    = os.getenv("PROVIDER", "openai")
        self.providerMap = {
            "openai": self.runOpenai,
            "google": self.runGoogle,
        }

    def run(self, systemMsg, userMsg):
        try:
            return self.providerMap[self.provider](systemMsg, userMsg)
        except KeyError:
            raise ValueError("Invalid LLM provider. Use 'openai' or 'google'.")

    def runOpenai(self, systemMsg, userMsg):
        prompt = [
            graph.handleJsonFormat("system", systemMsg),
            graph.handleJsonFormat("user", userMsg)
        ]
        return gptClient.chat.completions.create(
            model="gpt-4.1-mini",
            messages=prompt,
        ).choices[0].message.content

    def runGoogle(self, systemMsg, userMsg):
        system = [graph.handleTypedFormat("system", systemMsg)]
        model = "gemini-2.5-flash-preview-04-17"
        contents = []
        contents.append(graph.handleTypedFormat("user", userMsg))

        generateContentConfig = types.GenerateContentConfig(
            response_mime_type="text/plain",
            system_instruction=system,  # List of Parts
        )
        return genClient.models.generate_content(
            model=model,
            contents=contents,
            config=generateContentConfig,
        ).text


class SubMinion:
    def __init__(self, task, minionName):
        self.minionTool = MinionTool()
        self.task      = task
        self.minionName = minionName

    def run(self, verbose=False):
        clarified = self.minionTool.run(skillInstructions, self.task)
        if verbose:
            print(f"[{self.minionName}] Clarified action: {clarified}")
        actions = graph.getActions(clarified)
        allSkills = graph.getMinionActions()
        results = graph.executeActions(allSkills, actions)
        filtered = [str(r) for r in results if r]
        finalResult = "\n".join(filtered)
        if verbose:
            print(f"Executed actions, got:\n{finalResult} Bello!")
        return finalResult or "No action result. Banana!"


class OrchestratorMinion:
    def __init__(self):
        self.minionTool = MinionTool()

    def decomposeSteps(self, userGoal):
        availableActions = graph.getMinionActions()
        prompt = (
            "Given the following available actions:\n"
            f"{', '.join(availableActions)}\n"
            "If the goal can be answered directly without calling any of these actions, say 'NO ACTIONS NEEDED'.\n"
            "Otherwise, break down the goal into the MINIMUM number of direct function calls, each matching exactly one of the available actions. "
            "If an action can't be matched directly, SKIP that step. "
            "Do NOT include high-level or abstract instructions. "
            "Just output a bullet list, one per function call, e.g.:\n"
            "- get_temperature(47.6588, -117.4260)\n"
            f"Goal: {userGoal}"
        )
        stepsText = self.minionTool.run("You are an expert orchestrator minion.", prompt)
        steps = [line.lstrip("-1234567890. ").strip() for line in stepsText.splitlines() if line.strip()]
        return steps

    def run(self, mainMinion, userGoal, verbose=False):
        steps = self.decomposeSteps(userGoal)
        results = []
        stepsClean = [s.lower().strip() for s in steps]
        if not steps or any("no action" in s for s in stepsClean):
            if verbose:
                print(f"\n[{mainMinion}] No sub-minions needed! Bello! I answer directly, banana!")
            answer = self.minionTool.run(
                "You are a helpful minion who answers questions directly if no tools/actions are required.",
                f"Answer this question in a fun minion way: \"{userGoal}\". Always end with a minion quote like: 'Bello!'"
            )
            return [{"step": "direct_answer", "result": answer}]
        for i, step in enumerate(steps, 1):
            subMinionName = SUB_MINIONS[(i - 1) % len(SUB_MINIONS)]
            if verbose:
                print(f"\n[{mainMinion}] Executing sub-minion [{subMinionName}] for task: {step} Bello!")
            subMinion = SubMinion(step, subMinionName)
            result = subMinion.run(verbose=verbose)
            results.append({"step": step, "result": result})
        return results

class MainMinion:
    def __init__(self):
        self.orchestrator = OrchestratorMinion()
        self.minionTool    = MinionTool()

    def processInput(self, userGoal, verbose=False):
        def llm(prompt):
            return self.minionTool.run("You are a helpful minion.", prompt)
        if verbose:
            print(f"\nBello!!! Banana!!!\n")
        prompt = (
            "You are a helpful minion. Restate the following user goal as a single clear task.\n"
            f"User Goal: {userGoal}"
        )
        clarifiedGoal = llm(prompt)
        mainMinion = MAIN_MINIONS[random.randint(0, len(MAIN_MINIONS) - 1)]
        if verbose:
            print(f"[{mainMinion}]: {clarifiedGoal}")
        results = self.orchestrator.run(mainMinion, clarifiedGoal, verbose=verbose)
        resultsSummary = "\n".join(
            f"{r['step']}: {r['result']}" for r in results
        )
        minionPersonality = (
            "Respond as if you are a Minion from the Minions movie. "
            "Be silly, use funny minion phrases, sound happy, and always end with a minion quote! "
            "Example ending: 'Bello!'\n"
            "Mix some minion language (like 'banana', 'bello', 'poopaye', etc) with your answer, but still answer the user's question clearly.\n"
        )
        answer = llm(
            f"{minionPersonality}"
            f"User originally asked: \"{userGoal}\"\n"
            f"Here are the results for that request:\n{resultsSummary}\n"
            "Write your response now!"
        )
        print(f"\n[{mainMinion}]\n{answer}")
        return f"[{mainMinion}] {answer}\n"
