import spade
import asyncio
import os
import argparse
from user1_agent import UserAgentOne
from user2_agent import UserAgentTwo
from user3_agent import UserAgentThree
from user4_agent import UserAgentFour
from coordinator_agent import CoordinatorAgent


async def main():
    parser = argparse.ArgumentParser(description="Scheduling meetings with the option of preference.")
    parser.add_argument("-preference", action="store_true", help="This executes the scheduling with agent preferences.")
    args = parser.parse_args()

    user_agent1 = UserAgentOne("user1@localhost", "password", args.preference)
    user_agent2 = UserAgentTwo("user2@localhost", "password", args.preference)
    user_agent3 = UserAgentThree("user3@localhost", "password", args.preference)
    user_agent4 = UserAgentFour("user4@localhost", "password", args.preference)
    coordinator_agent = CoordinatorAgent("coordinator@localhost", "password")
    
    file_path = "user_agents.txt"
    if os.path.exists(file_path):
        with open("user_agents.txt", "r+") as file:
            file.truncate()

    await user_agent1.start()
    await user_agent2.start()
    await user_agent3.start()
    await user_agent4.start()
    await coordinator_agent.start()
    
    await asyncio.sleep(5)

    await spade.wait_until_finished(user_agent1)
    await spade.wait_until_finished(user_agent2)
    await spade.wait_until_finished(user_agent3)
    await spade.wait_until_finished(user_agent4)
    await coordinator_agent.stop()

    print("Program completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())

