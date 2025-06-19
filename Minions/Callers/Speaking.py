import random
import os
from dotenv import load_dotenv

from Utils.Names import MAIN_MINIONS, SUB_MINIONS
from Utils.Voices import MinionVoices
from Utils.SkillGraph import SkillGraph
from AgentToAgent import AgentToAgent

from openai import OpenAI
from google import genai
from google.genai import types

load_dotenv()
gptClient = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
genClient = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

graph = SkillGraph()
skillInstructions = graph.skillInstructions()
ROUNDS = 10


class MinionMessageBus:
    def __init__(self):
        self.ata = AgentToAgent()
        self.minionVoices = MinionVoices()

    def mainSpeak(self, text, rate=250, pitch=150, volume=0.5):
        self.minionVoices.mainSpeak(text, rate, pitch, volume)

    def subSpeak(self, text, rate=300, pitch=150, volume=0.5):
        self.minionVoices.subSpeak(text, rate, pitch, volume)

    def send(self, fromAgent, toAgent, content):
        self.ata.send(fromAgent, toAgent, content)

    def receive(self, minionName, allowedFrom=None):
        return self.ata.receive(minionName, allowedFrom)


class MinionTool:
    def __init__(self):
        self.provider = os.getenv("PROVIDER", "openai")
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
            system_instruction=system,
        )
        return genClient.models.generate_content(
            model=model,
            contents=contents,
            config=generateContentConfig,
        ).text


class SubMinion:
    def __init__(self, task, minionName, messageBus):
        self.minionTool = MinionTool()
        self.task = task
        self.minionName = minionName
        self.bus = messageBus
        self.result = None
        self.state = {}
        self.completed = False
        self.subMinionTasks = None
        self.delegatedTo = None

    def sendMessage(self, to, content):
        self.bus.send(self.minionName, to, content)

    def receiveMessages(self):
        return self.bus.receive(self.minionName)

    def needsDataFrom(self):
        if not self.subMinionTasks or len(self.subMinionTasks) <= 1:
            return []
        myTask = self.task
        otherTasks = [
            f"{name}: {task}"
            for name, task in self.subMinionTasks.items() if name != self.minionName
        ]
        prompt = (
            f"You are a minion. Your current task is:\n{myTask}\n"
            f"Here are the tasks of your fellow minions:\n" +
            "\n".join(otherTasks) +
            "\n\nList the NAMES of any minions whose task you need to see before completing your own. "
            "Only respond with a comma-separated list of minion names. If none, respond with NONE."
        )
        answer = self.minionTool.run(
            "You are a minion determining your dependencies.",
            prompt
        )
        names = [n.strip() for n in answer.split(",") if n.strip() and n.strip().upper() != "NONE"]
        return names

    def askForHelp(self):
        needed = self.needsDataFrom()
        for minionName in needed:
            self.sendMessage(minionName, f"Can you help me with your result for {self.subMinionTasks[minionName]}? Banana!")

    def maybeDelegate(self):
        # Only allow delegation if there are at least 3 minions (prevents infinite loops on two)
        if self.subMinionTasks and len(self.subMinionTasks) > 2 and random.random() < 0.80:
            others = [name for name in self.subMinionTasks if name != self.minionName]
            if others:
                chosen = random.choice(others)
                # Prevent delegating back and forth endlessly
                if self.delegatedTo == chosen:
                    return False
                self.delegatedTo = chosen
                self.sendMessage(chosen, f"Bello! Me want {self.task}! You do, okie dokie? Banana!")
                self.completed = True
                self.result = f"Delegated to {chosen} Bello!"
                return True
        return False

    def runStep(self, verbose=False):
        if not self.completed and not self.maybeDelegate():
            clarified = self.minionTool.run(skillInstructions, self.task)
            if verbose:
                self.bus.subSpeak(f"[{self.minionName}] Running step: {clarified}")
            else:
                print(f"\n[{self.minionName}] Clarified action: {clarified}")
            actions = graph.getActions(clarified)
            allSkills = graph.getMinionActions()
            results = graph.executeActions(allSkills, actions)
            filtered = [str(r) for r in results if r]
            finalResult = "\n".join(filtered)
            if verbose:
                self.bus.subSpeak(f"[{self.minionName}] Executed actions, got:\n{finalResult} Bello!")
            else:
                print(f"Executed actions, got:\n{finalResult}")
            self.result = finalResult or "No action result."
            self.completed = True
            self.sendMessage(None, f"Done with: {self.task} Bello!")

    def processMessages(self, verbose=False):
        newMessages = self.receiveMessages()
        for m in newMessages:
            if verbose:
                self.bus.subSpeak(f"[{self.minionName}] Message from {m['from']}: {m['content']}")
            else:
                print(f"\n[{self.minionName}] Message from {m['from']}: {m['content']}")
            if "Me want" in m['content']:
                task = m['content'].split("Me want", 1)[-1].strip()
                if "!" in task:
                    task = task.split("!", 1)[0].strip()
                clarified = self.minionTool.run(skillInstructions, task)
                actions = graph.getActions(clarified)
                allSkills = graph.getMinionActions()
                results = graph.executeActions(allSkills, actions)
                filtered = [str(r) for r in results if r]
                finalResult = "\n".join(filtered)
                reply = f"Did your lazy task: {task}\nResult: {finalResult or 'No action result.'} Bello!"
                self.sendMessage(m['from'], reply)
            elif "Can you help" in m['content']:
                reply = f"\nSure, {m['from']}! Here's my result for {self.task}: {self.result or 'not ready yet!'} Banana!"
                self.sendMessage(m['from'], reply)
            elif "Here's" in m['content'] or "Done with" in m['content']:
                self.state[m['from']] = m['content']


class OrchestratorMinion:
    def __init__(self):
        self.minionTool = MinionTool()
        self.bus = MinionMessageBus()
        self.subagents = {}

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
                self.bus.mainSpeak(f"\n[{mainMinion}] No subminions needed! I'll answer directly, Bello!")
            else:
                print(f"\n[{mainMinion}] No subminions needed! I'll answer directly, Bello!")
            answer = self.minionTool.run(
                "You are a helpful minion who answers questions directly if no tools/actions are required.",
                f"Answer this question in a fun minion way: \"{userGoal}\". Always end with a minion quote like: 'Bello!'"
            )
            return [{"step": "direct_answer", "result": answer}]

        self.subagents = {}
        subagentTasks = {}
        for i, step in enumerate(steps, 1):
            subMinionName = SUB_MINIONS[(i - 1) % len(SUB_MINIONS)]
            self.subagents[subMinionName] = SubMinion(step, subMinionName, messageBus=self.bus)
            subagentTasks[subMinionName] = step

        for agent in self.subagents.values():
            agent.subagentTasks = subagentTasks

        if verbose:
            self.bus.mainSpeak(f"\n[{mainMinion}] Decomposed steps: {', '.join(steps)}")
        else:
            print(f"\n[{mainMinion}] === Bello! Calling Minions! ===")

        for roundNum in range(ROUNDS):
            for agent in self.subagents.values():
                agent.processMessages(verbose=verbose)
            if roundNum == 0:
                for agent in self.subagents.values():
                    agent.runStep(verbose=verbose)
            if roundNum == 1:
                for agent in self.subagents.values():
                    agent.askForHelp()
            if roundNum >= 2:
                anyMessages = any(agent.receiveMessages() for agent in self.subagents.values())
                if not anyMessages and all(m.completed for m in self.subagents.values()):
                    break

        for agent in self.subagents.values():
            agent.processMessages(verbose=verbose)
            # Only set results to actual output, not delegated message
            agentResult = agent.result
            if agentResult and agentResult.startswith("Delegated to "):
                # Try to resolve the actual result from agent.state
                for val in agent.state.values():
                    if "Result:" in val:
                        agentResult = val.split("Result:")[-1].strip()
            results.append({"step": agent.task, "result": agentResult})

        return results


class MainMinion:
    def __init__(self):
        self.orchestrator = OrchestratorMinion()
        self.minionTool = MinionTool()

    def processInput(self, userGoal, verbose=False):
        def llm(prompt):
            return self.minionTool.run("You are a helpful minion.", prompt)
        if verbose:
            self.orchestrator.bus.mainSpeak(f"\nBello!!! Banana!!!\n")
        else:
            print("\nBello!!! Banana!!!\n")
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
        if verbose:
            self.orchestrator.bus.mainSpeak(f"\n[{mainMinion}]\n{answer}")
        else:
            print(f"\n[{mainMinion}]\n{answer}")
        return f"[{mainMinion}] {answer}\n"

# # Usage:
# if __name__ == "__main__":
#     mainMinion = MainMinion()
#     while True:
#         userGoal = input("\nEnter your goal (or 'exit' to quit): ").strip()
#         if userGoal.lower() == 'exit':
#             print("Exiting the minion. Bello!")
#             break
#         if not userGoal:
#             print("Please enter a valid goal. Banana!")
#             continue
#         mainMinion.processInput(userGoal, verbose=True)
