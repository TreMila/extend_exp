import requests
import json
from tqdm import tqdm

URI = 'api_for_alpaca_33B'

with open('../CASIE/processed_data/dev_input_list.txt','r',encoding='utf-8') as f:
    dev_input_list = [item.strip('\n') for item in f.readlines()]

with open('../CASIE/processed_data/labels.txt', 'r', encoding='utf-8') as f:
    event_type_list = [item.strip('\n') for item in f.readlines()]

with open('./data/casie/input_list.txt','r',encoding='utf-8') as f:
    input_list = [item.strip('\n') for item in f.readlines()]

with open('./data/casie/final_event_extend_map_alpaca_33B_en.json','r',encoding='utf-8') as f:
    event_extend_map = json.load(f)

with open('./data/casie/cots.txt','r',encoding='utf-8') as f:
    cots = [eval(line) for line in f]


input_list2eve={}
for idx, item in enumerate(input_list):
    input_list2eve[item] = event_type_list[idx//10]

id2dev_input_list = {}
for idx, item in enumerate(dev_input_list):
    id2dev_input_list[idx] = item

def get_sys_prompt(cot):
    return(f'''You are currently an expert in extracting event-triggered words.

Your task is to extract the trigger words that match the event type given the text and event type, and follow the following rules when generating

1. Based on the given event type, combined with the context of the given text, extract the trigger word span that may exist in the given event type
2. Generate judgment sentences based on the paired event type and event trigger word span, and check whether each judgment sentence is correct, and only output "yes" or "no"
3. Generate an event detection list according to the judgment sentence, (event type, event trigger span), where the event type must be a given event type

The following is an example of a chain of thought to help you think step by step to solve the above problems
Text: "{id2dev_input_list[cot[0]]}" Event type: [{cot[1]}]

Trigger span: [{cot[2]}]
answer:
Is the trigger word for event type "{cot[1]}" "{cot[2]}"? yes

Generate a list of event detections:
``
({cot[1]}, {cot[2]})
``''')


def get_backward_prompt(example, extend_eve):
    return(f'''Text: "{example}" Event type: [{extend_eve}]''')


def call_api(prompt, p):
    request = {
        'messages': prompt,
        'max_tokens': 2000,
        'top_p': p,
    }
    response = requests.post(URI, json=request)

    if response.status_code == 200:
        result = response.json()['choices']
        return result[-1]['message']['content']


def run(input_list, input_list2eve, event_extend_map, cots, mode):
    for idx, example in tqdm(enumerate(input_list), total=len(input_list), desc="Processing..."):
        event = input_list2eve[example]
        event_extend = event_extend_map[event]
        cot = cots[idx]

        for e in event_extend:
            msg_list=[
                {"role": "system", "message": get_sys_prompt(cot)},
                {"role": "user", "message": get_backward_prompt(example, e)},
            ]
            rsp_1 = call_api(msg_list, 0.3) 
            rsp_2 = call_api(msg_list, 0.6)
            rsp_3 = call_api(msg_list, 1)
            backward_details_path = f'./results/details_{mode}.txt'
            with open(backward_details_path, 'a', encoding='utf-8') as f:
                f.write(str(idx+1) + "：\nOutput:" + rsp_1 + "\nOutput:" + rsp_2 + "\nOutput:" + rsp_3 + "\n\n")


def run_gold(input_list, input_list2eve, cots, mode):
    for idx, example in tqdm(enumerate(input_list), total=len(input_list), desc="Processing..."):
        event = input_list2eve[example]
        cot = cots[idx]

        msg_list=[
            {"role": "system", "message": get_sys_prompt(cot)},
            {"role": "user", "message": get_backward_prompt(example, event)},
        ]
        rsp_1 = call_api(msg_list, 0.3) 
        rsp_2 = call_api(msg_list, 0.6)
        rsp_3 = call_api(msg_list, 1)
        backward_details_path = f'./results/details_gold_{mode}.txt'
        with open(backward_details_path, 'a', encoding='utf-8') as f:
            f.write(str(idx+1) + "：\nOutput:" + rsp_1 + "\nOutput:" + rsp_2 + "\nOutput:" + rsp_3 + "\n\n")


run(input_list, input_list2eve, event_extend_map, cots, 'alpaca_33B_en')
run_gold(input_list, input_list2eve, cots, 'alpaca_33B_en')