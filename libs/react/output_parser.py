"""ReAct output parser."""


import ast
import json
import re
from typing import Tuple

from libs.react.types import (
    ActionReasoningStep,
    ActionReasoningStepArr,
    BaseReasoningStep,
    ResponseReasoningStep,
)
from llama_index.output_parsers.utils import extract_json_str
from llama_index.types import BaseOutputParser


def extract_tool_use_1(input_text: str) -> Tuple[str, str, str]:
    pattern = r"\s*Thought 1:(.*?)Action 1:(.*?)Action Input 1:(.*?)(?:\n|$)"

    match = re.search(pattern, input_text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not extract tool use from input text: {input_text}")

    try:
        thought = match.group(1).strip()
    except:
        thought = ""
    action = match.group(2).strip()
    action_input = match.group(3).strip()
    return thought, action, action_input


def extract_tool_use_2(input_text: str) -> Tuple[str, str, str]:
    pattern = r"\s*(?:Thought 2:)?(.*?)Action 2:(.*?)Action Input 2:(.*?)(?:\n|$)"

    match = re.search(pattern, input_text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not extract tool use from input text: {input_text}")

    try:
        thought = match.group(1).strip()
    except:
        thought = ""
    action = match.group(2).strip()
    action_input = match.group(3).strip()
    return thought, action, action_input


def extract_tool_use_3(input_text: str) -> Tuple[str, str, str]:
    pattern = r"\s*(?:Thought 3:)?(.*?)Action 3:(.*?)Action Input 3:(.*?)(?:\n|$)"

    match = re.search(pattern, input_text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not extract tool use from input text: {input_text}")

    try:
        thought = match.group(1).strip()
    except:
        thought = ""
    action = match.group(2).strip()
    action_input = match.group(3).strip()
    return thought, action, action_input


def extract_tool_use_4(input_text: str) -> Tuple[str, str, str]:
    pattern = r"\s*(?:Thought 4:)?(.*?)Action 4:(.*?)Action Input 4:(.*?)(?:\n|$)"

    match = re.search(pattern, input_text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not extract tool use from input text: {input_text}")

    try:
        thought = match.group(1).strip()
    except:
        thought = ""
    action = match.group(2).strip()
    action_input = match.group(3).strip()
    return thought, action, action_input


def extract_tool_use_5(input_text: str) -> Tuple[str, str, str]:
    pattern = r"\s*(?:Thought 5:)?(.*?)Action 5:(.*?)Action Input 5:(.*?)(?:\n|$)"

    match = re.search(pattern, input_text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not extract tool use from input text: {input_text}")

    try:
        thought = match.group(1).strip()
    except:
        thought = ""
    action = match.group(2).strip()
    action_input = match.group(3).strip()
    return thought, action, action_input


def extract_final_response(input_text: str) -> Tuple[str, str]:
    pattern = r"\s*Thought 1:(.*?)Answer:(.*?)(?:$)"

    match = re.search(pattern, input_text, re.DOTALL)
    if not match:
        raise ValueError(
            f"Could not extract final answer from input text: {input_text}"
        )

    thought = match.group(1).strip()
    answer = match.group(2).strip()
    return thought, answer


class ReActOutputParser(BaseOutputParser):
    """ReAct Output parser."""

    def parse(self, output: str, is_streaming: bool = False) -> BaseReasoningStep:
        """Parse output from ReAct agent.

        We expect the output to be in one of the following formats:
        1. If the agent need to use a tool to answer the question:
            ```
            Thought: <thought>
            Action: <action>
            Action Input: <action_input>
            ```
        2. If the agent can answer the question without any tools:
            ```
            Thought: <thought>
            Answer: <answer>
            ```
        """

        # print("output_xxxxxxxxxxxxxxxxx: ", output)
        if (
            all(
                thought not in output
                for thought in ["Thought 1", "Thought 2", "Thought 3"]
            )
            and "Answer:" not in output
        ):
            # NOTE: handle the case where the agent directly outputs the answer
            # instead of following the thought-answer format
            return ResponseReasoningStep(
                thought="(Implicit) I can answer without any more tools!",
                response=output,
                is_streaming=is_streaming,
            )

        if "Answer:" in output:
            thought, answer = extract_final_response(output)
            return ResponseReasoningStep(
                thought=thought, response=answer, is_streaming=is_streaming
            )

        thoughts = []
        actions = []
        action_inputs = []
        if "Action 1:" in output:
            # thought, action, action_input = extract_tool_use(output)
            thought1, action1, action_input1 = extract_tool_use_1(output)
            # print("action_input1: ", action_input1)
            # print("thought1: ", thought1)
            # print("action1: ", action1)
            json_str1 = extract_json_str(action_input1)

            # First we try json, if this fails we use ast
            try:
                action_input_dict1 = json.loads(json_str1)
            except json.JSONDecodeError:
                action_input_dict1 = ast.literal_eval(json_str1)

            thoughts.append(thought1)
            actions.append(action1)
            action_inputs.append(action_input_dict1)

        if "Action 2:" in output:
            # thought, action, action_input = extract_tool_use(output)
            thought2, action2, action_input2 = extract_tool_use_2(output)
            json_str2 = extract_json_str(action_input2)

            # First we try json, if this fails we use ast
            try:
                action_input_dict2 = json.loads(json_str2)
            except json.JSONDecodeError:
                action_input_dict2 = ast.literal_eval(json_str2)

            thoughts.append(thought2)
            actions.append(action2)
            action_inputs.append(action_input_dict2)

        if "Action 3:" in output:
            # thought, action, action_input = extract_tool_use(output)
            thought3, action3, action_input3 = extract_tool_use_3(output)
            json_str3 = extract_json_str(action_input3)

            # First we try json, if this fails we use ast
            try:
                action_input_dict3 = json.loads(json_str3)
            except json.JSONDecodeError:
                action_input_dict3 = ast.literal_eval(json_str3)

            thoughts.append(thought3)
            actions.append(action3)
            action_inputs.append(action_input_dict3)

        if "Action 4:" in output:
            # thought, action, action_input = extract_tool_use(output)
            thought4, action4, action_input4 = extract_tool_use_4(output)
            json_str4 = extract_json_str(action_input4)

            # First we try json, if this fails we use ast
            try:
                action_input_dict4 = json.loads(json_str4)
            except json.JSONDecodeError:
                action_input_dict4 = ast.literal_eval(json_str4)

            thoughts.append(thought4)
            actions.append(action4)
            action_inputs.append(action_input_dict4)

        if "Action 5:" in output:
            # thought, action, action_input = extract_tool_use(output)
            thought5, action5, action_input5 = extract_tool_use_5(output)
            json_str5 = extract_json_str(action_input5)

            # First we try json, if this fails we use ast
            try:
                action_input_dict5 = json.loads(json_str5)
            except json.JSONDecodeError:
                action_input_dict5 = ast.literal_eval(json_str5)

            thoughts.append(thought5)
            actions.append(action5)
            action_inputs.append(action_input_dict5)

        return ActionReasoningStepArr(
            thoughts=thoughts, actions=actions, action_inputs=action_inputs
        )

        raise ValueError(f"Could not parse output: {output}")

    def format(self, output: str) -> str:
        """Format a query with structured output formatting instructions."""
        raise NotImplementedError
