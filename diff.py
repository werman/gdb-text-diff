import gdb
import gdb.types
import gdb.printing
import gdb.command

import os
import tempfile

from collections import namedtuple

TrackedValue = namedtuple('TrackedValue',
                          ['gdb_value', 'print_func', 'id',
                           'values_history', 'file_prev', 'file_cur'])


class DiffCommand(gdb.Command):
    '''
    Use this command to see the changes in text representation
    of specified expression.

    List of diff subcommands:

    diff add    - expression print_function identifier
        Will create two files with previous and current text
        representation of the specified expression.

        print_function - existing function which takes one
                         argument of the same type as expression

    diff remove - identifier
    '''

    ACTION_ADD = "add"
    ACTION_REMOVE = "remove"

    def __init__(self):
        super(DiffCommand, self).__init__("diff",
                                          gdb.COMMAND_DATA,
                                          gdb.COMPLETE_SYMBOL)

        self.dont_repeat()

        self._event_handler_registered = False
        self._tracked_values = []

    def invoke(self, arg, from_tty):
        """
        Called by GDB whenever this command is invoked.
        """

        args = gdb.string_to_argv(arg)

        action_type = str(args[0])
        if action_type == self.ACTION_ADD:
            if len(args) != 4:
                gdb.write(
                    "Incorrect number of arguments, expected 4", gdb.STDOUT)

            var_name = str(args[1])
            print_func = str(args[2])
            identifier = str(args[3])

            try:
                gdb_value = gdb.parse_and_eval(var_name)

                path_prev = os.path.join(
                    tempfile.gettempdir(), "gdb_diff_" + identifier + "_PREV.txt")
                path_cur = os.path.join(tempfile.gettempdir(
                ), "gdb_diff_" + identifier + "_CURRENT.txt")

                try:
                    file_prev = open(path_prev, "w")
                    file_cur = open(path_cur, "w")
                except IOError:
                    gdb.write("Cannot open \"{}\" or \"{}\" for writing".format(
                        path_prev, path_cur), gdb.STDOUT)
                    return

                tracked_value = TrackedValue(gdb_value=gdb_value,
                                             print_func=print_func,
                                             id=identifier,
                                             values_history=[],
                                             file_prev=file_prev,
                                             file_cur=file_cur)
                self._tracked_values.append(tracked_value)

                gdb.write("Tracking \"{}\", use your favourite diff application for:\n".format(
                    var_name), gdb.STDOUT)
                gdb.write("\t{}\n".format(path_prev), gdb.STDOUT)
                gdb.write("\t{}\n".format(path_cur), gdb.STDOUT)

                self.eval_value(tracked_value)
            except RuntimeError:
                gdb.write("\"{}\" is invalid variable to watch".format(
                    var_name), gdb.STDOUT)
                return

        elif action_type == self.ACTION_REMOVE:
            if len(args) != 2:
                gdb.write(
                    "Incorrect number of arguments, expected 2", gdb.STDOUT)

            identifier = str(args[1])

            idx = next((i for i, x in enumerate(
                self._tracked_values) if x.id == identifier), None)

            if idx is None:
                gdb.write("Unknown identifier \"{}\"".format(
                    identifier), gdb.STDOUT)
            else:
                self._tracked_values[idx].file_prev.close()
                self._tracked_values[idx].file_cur.close()
                del self._tracked_values[idx]

                gdb.write("Removed \"{}\"".format(identifier), gdb.STDOUT)

        else:
            gdb.write("Unknown action {}".format(action_type), gdb.STDOUT)
            return

        if not self._event_handler_registered:
            gdb.events.stop.connect(self.stop_handler)
            gdb.events.exited.connect(self.exit_handler)
            self._event_handler_registered = True

    def stop_handler(self, event):
        """
        The debugger has stopped (e.g. a breakpoint was hit).
        """

        for tracked_value in self._tracked_values:
            self.eval_value(tracked_value)

    def exit_handler(self, event):
        for tracked_value in self._tracked_values:
            tracked_value.file_prev.close()
            tracked_value.file_cur.close()

        self._tracked_values.clear()

    def eval_value(self, tracked_value):
        eval_expr = "{} (({}) {})".format(tracked_value.print_func,
                                          str(tracked_value.gdb_value.type),
                                          str(int(tracked_value.gdb_value)))

        eval_result_str = None
        try:
            eval_result = gdb.parse_and_eval(eval_expr)
            eval_result_str = eval_result.string()
        except RuntimeError:
            gdb.write("Unable to evaluate \"{}\"".format(
                eval_expr), gdb.STDOUT)
            return

        if eval_result_str is not None:
            if len(tracked_value.values_history) == 0 or tracked_value.values_history[-1] != eval_result_str:
                tracked_value.values_history.append(eval_result_str)

                if len(tracked_value.values_history) > 1:
                    tracked_value.file_prev.seek(0)
                    tracked_value.file_prev.write(
                        tracked_value.values_history[-2])
                    tracked_value.file_prev.truncate()
                    tracked_value.file_prev.flush()

                tracked_value.file_cur.seek(0)
                tracked_value.file_cur.write(tracked_value.values_history[-1])
                tracked_value.file_cur.truncate()
                tracked_value.file_cur.flush()


DiffCommand()
