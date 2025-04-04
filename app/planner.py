import os
import json
import platform
from openai import OpenAI

class planner:
    """
    Parameters:
    - planner_api_key (str): API key for the planner client
    - planner_base_url (str): Base URL for the planner client
    - planner_model (str): Model to be used by the planner client
    - query (str): The user's query

    Returns:
    - completion (str): The full output of LLM
    - thinking (str): LLM's thinking process
    - tasks (arr): The task List generated by LLM
    """
    def __init__(self, planner_api_key, planner_base_url, planner_model):
        self.planner_client = OpenAI(
            api_key=planner_api_key,
            base_url=planner_base_url,
        )
        self.planner_model = planner_model
        self.controlledOS = platform.system()
        self.run_folder = os.environ["RUN_FOLDER"]

    def _get_system_prompt(self):
        return f"""
You are a planner.
You need to help me use {self.controlledOS} system according to the following information.
You need to imitate the actions of humans operating computers to split tasks.
When you need to write a file such as word or excel, use code to write it instead of opening the software to operate it.

## Output format:
```json
{{
    "thinking": "Describe your thoughts on how to achieve the user's query.",
    "tasks":  ["task description", "task description"]
}}
```

## Output example1:
```json
{{
    "thinking": "In order to play Bilibili's 'apex' video, I need to open the Bilibili website first, and then search for apex related videos, click one of them to play.",
    "tasks":  ["Search and enter the 'https://www.bilibili.com/' website", "Search 'apex' in the search box and confirm", "Click on the first video to play"]
}}
```
## Output example2:
```json
{{
    "thinking": "In order to organize the ranking information of the global rich list into the excel table, I need to open the browser, search the global rich list, extract the information related to the global rich list, and use the code to generate an excel file.",
    "tasks":  ["Press ['win', 'd'] to return to the desktop", "open the browser", "Search and enter the 'https://www.forbes.com/billionaires/' website", "Extract the information related to the global rich list", "Press ['win', 'd'] to return to the desktop", "Generate excel files using code"]
}}
```

## Note:
- When you need to search for content on the Web, you will first open a search result that contains multiple pages, and you need to click on the right page first to get the relevant information.
- Make sure to return to the desktop before opening any software, and then look for opening it. Use the ['win', 'd'] shortcut keys to return to the desktop under Windows system.
- If the task you perform is related to the current interface, please do not return to desktop.
- Since each task will be used separately, please avoid the situation where there are only instructions and no objects. For example, if you need to use code to generate files, please indicate the xx information you obtained before.
"""


    def _parse_tasks(self, content):
        json_str = content.replace("```json","").replace("```","").strip()
        json_dict = json.loads(json_str)
        return json_dict["thinking"], json_dict["tasks"]

    def __call__(self, query):
        messages=[
            {
                "role": "system",
                "content": self._get_system_prompt(),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                ],
            }
        ]
        completion = self.planner_client.chat.completions.create(
            model=self.planner_model,
            messages=messages
        )
        content = completion.choices[0].message.content
        thinking, tasks = self._parse_tasks(content)
        
        with open(os.path.join(self.run_folder, 'memory.json'), 'r+') as memory_file:
            memory_data = json.load(memory_file)
            # Convert string tasks to objects with "task" key
            task_objects = [{"task": task} for task in tasks]
            memory_data["tasks"].extend(task_objects)
            memory_file.seek(0)
            json.dump(memory_data, memory_file, indent=4)
            memory_file.truncate()
        
        return completion, thinking, tasks
