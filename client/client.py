from __future__ import annotations

import json
import logging
import shlex
import threading
from collections.abc import Callable
from functools import wraps
from subprocess import PIPE, Popen, TimeoutExpired
from typing import ParamSpec, TypeVar

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

from .SockClient import SockClient

P = ParamSpec("P")
R = TypeVar("R")


def logged(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def fn(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except Exception:
            logging.exception("Ran into an exception in %s", func.__name__)
            raise
    return fn


def run_test(testcase: TestCase, cmd: list[str]) -> RunResult:
    with Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
        try:
            (stdout_data, stderr_data) = proc.communicate(testcase.test_in.encode(), timeout=2)
        except TimeoutExpired:
            proc.kill()
            (stdout_data, stderr_data) = proc.communicate()

    return RunResult(testcase, stdout_data.decode(), stderr_data.decode())


class TestResultsScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    def __init__(self, results: list[RunResult]):
        super().__init__()
        self.results = results

    def compose(self) -> ComposeResult:
        yield Header()
        for result in self.results:
            yield Static(result.show())


class ClashStatic(Static):
    def __init__(self, txt: str, **kwargs):
        super().__init__(txt, **kwargs, markup=False)

    def set_content(self, txt: str) -> None:
        txt = txt.replace("{{", "").replace("}}", "")
        txt = txt.replace("<<", "").replace(">>", "")
        txt = txt.replace("[[", "").replace("]]", "")
        self.update(txt)


class RoundEndScreen(Screen):
    # TODO: maybe it's not good to make it so easy to accidentally quit
    # maybe could make a thing to toggle the results from previous round
    # whenever?
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]

    def __init__(self, submissions: list[dict[str, str]]):
        super().__init__()
        self.submissions = [Submission(subm) for subm in submissions]

    def compose(self) -> ComposeResult:
        yield Header()
        code = self.submissions[0].code if self.submissions else "no submissions"
        yield Horizontal(
            ListView(*self.submissions, id="submission-list"),
            Static(code, id="code", expand=True),
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if not isinstance(event.item, Submission):
            return
        code_view = self.query_one("#code", Static)
        code_view.update(event.item.code)


class Submission(ListItem):
    def __init__(self, submission_obj: dict[str, str]):
        super().__init__()
        self.author = submission_obj["author"]
        self.code = submission_obj["code"]
        self.cmd = submission_obj["command"]

    def compose(self) -> ComposeResult:
        # TODO: figure out a good way to show cmd too
        yield Label(self.author)


class RunResult:
    def __init__(self, testcase: TestCase, stdout_data: str, stderr_data: str):
        self.testcase = testcase
        self.stdout = stdout_data
        self.stderr = stderr_data
        self.success = testcase.test_out.rstrip() == stdout_data.rstrip()

    def show(self) -> str:
        if self.success:
            success = "PASSED"
        else:
            # TODO: print a nice diff
            reason = "get good"
            success = f"FAILED\n  {reason}"
        return f"{self.testcase.title}: {success}\n"


class TestCase(ListItem):
    def __init__(self, testobj: dict[str, str]):
        super().__init__()
        self.title = testobj["title"]
        self.test_in = testobj["testIn"]
        self.test_out = testobj["testOut"]

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static(self.test_in, classes="test-text"),
            Static(self.test_out, classes="test-text"),
        )


class PuzzleWidget(Widget):
    def __init__(self) -> None:
        super().__init__()
        self.puzzle_title = Label("Puzzle Title", classes="statement-title", id="puzzle-title")
        self.statement = ClashStatic("statement", id="statement-text")
        self.constraints = ClashStatic("constraints", id="constraints")
        self.input_description = ClashStatic("input-description", id="input-description")
        self.output_description = ClashStatic("output-description", id="output-description")

    def compose(self) -> ComposeResult:
        yield Vertical(
            self.puzzle_title,
            self.statement,
            Label("\nConstraints:", classes="statement-title"),
            self.constraints,
            Label("\nInput Description:", classes="statement-title"),
            self.input_description,
            Label("\nOutput Description:", classes="statement-title"),
            self.output_description,
            id="statement",
        )

    def set_puzzle(self, puzzle: dict[str, str]) -> None:
        self.puzzle_title.update(puzzle["title"])
        self.statement.set_content(puzzle["statement"])
        self.constraints.set_content(puzzle.get("constraints", "None"))
        self.input_description.set_content(puzzle["inputDescription"])
        self.output_description.set_content(puzzle["outputDescription"])


class TuiClashApp(App):
    class PuzzleChanged(Message):
        def __init__(self, sender: TuiClashApp, puzzlemsg: str):
            super().__init__(sender)
            self.puzzle = json.loads(puzzlemsg)

    class RoundEnd(Message):
        def __init__(self, sender: TuiClashApp, submissions: str):
            super().__init__(sender)
            self.submissions = json.loads(submissions)

    CSS_PATH = "style.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Dark mode"),
        ("x", "set_puzzle", "Set puzzle"),
        ("s", "start_round", "Start a new round"),
    ]

    def __init__(self, host: str, port: int):
        super().__init__()
        self.client = SockClient(host, port)
        self.testcases = ListView(id="test-cases-list")
        self.puzzle = PuzzleWidget()
        self.cmd = Input("python3 $FILE", id="cmd-input")
        self.codefile = Input("sol.py", id="codefile-input")
        self.sub_title = "Not connected"

    def run(self, **kwargs) -> None:
        handler = threading.Thread(target=self.handle_connection, daemon=True)
        handler.start()
        super().run(**kwargs)

    @logged
    def handle_connection(self) -> None:
        # TODO: PROPER exception handling
        self.client.connect()
        addr, port = self.client.addr
        self.sub_title = f"Connected to {addr}:{port}"
        while True:
            # TODO: PROPER exception handling
            try:
                msg = self.client.recv()
            except Exception:
                self.sub_title = "Disconnected"
                raise
            logging.debug(msg)
            if msg.startswith("PUZZLE:{"):
                new_puzzle = msg.removeprefix("PUZZLE:")
                self.post_message_no_wait(self.PuzzleChanged(self, new_puzzle))
            elif msg.startswith("SUBMISSIONS:"):
                submissions_str = msg.removeprefix("SUBMISSIONS:")
                self.post_message_no_wait(self.RoundEnd(self, submissions_str))

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Vertical(self.testcases, id="test-cases"),
            self.puzzle,
            Horizontal(Button("Run tests"), self.cmd, self.codefile, id="bottombar"),
            id="app-grid",
        )
        yield Footer()

    def action_set_puzzle(self) -> None:
        with open("example.json", encoding="utf-8") as file:
            new_puzzle = file.read()
        self.post_message_no_wait(self.PuzzleChanged(self, new_puzzle))

    @logged
    def on_button_pressed(self, _message: Message) -> None:
        # TODO: make it not blocking
        cmd = self.cmd.value
        results = []
        cmd_tuple = shlex.split(cmd.replace("$FILE", self.codefile.value))
        for testcase in self.testcases.focusable_children:
            if isinstance(testcase, TestCase):
                run_result = run_test(testcase, cmd_tuple)
                results.append(run_result)

        if not results:
            return

        num_correct = sum(1 for r in results if r.success)
        self.push_screen(TestResultsScreen(results))
        logging.info("%d/%d tests correct", num_correct, len(results))
        if num_correct == len(results):
            with open(self.codefile.value, encoding="utf-8") as file:
                code = file.read()
            # TODO: create a Submission class with fancy things
            # TODO: get author name from somewhere (CLI parameter?)
            obj = {
                "author": "test",
                "code": code,
                "command": cmd,
                "time": None,
            }
            self.client.send(f"SUBMISSION:{json.dumps(obj)}")

    @logged
    def on_tui_clash_app_round_end(self, msg: RoundEnd) -> None:
        end_screen = RoundEndScreen(msg.submissions)
        self.push_screen(end_screen)

    @logged
    def on_tui_clash_app_puzzle_changed(self, msg: PuzzleChanged) -> None:
        puzzle = msg.puzzle
        data = puzzle["lastVersion"]["data"]
        self.puzzle.set_puzzle(data)

        testcases = data["testCases"]
        self.testcases.clear()
        for test in testcases:
            self.testcases.append(TestCase(test))

    def action_start_round(self) -> None:
        self.client.send("START ROUND")
