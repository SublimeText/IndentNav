from __future__ import annotations
import sublime
import sublime_plugin

__all__ = ["IndentMoveCommand"]


class IndentMoveCommand(sublime_plugin.TextCommand):
    def run(self, _, to: str, extend: bool = False) -> None:
        goto = getattr(self, "goto_" + to)
        if not goto:
            print(f'Command "{self.name()}" got invalid argument to="{to}"!')
            return

        forward = to in ("end", "next_sibling")
        rows = set()
        new_sels = []

        # perform operation for all carets and selections
        for sel in self.view.sel() if forward else reversed(self.view.sel()):
            sel = goto(sel, extend)
            row, _ = self.view.rowcol(sel.b)
            if row not in rows:
                rows.add(row)
                new_sels.append(sel)

        # update carets and selections
        if new_sels:
            self.view.sel().clear()
            self.view.sel().add_all(new_sels)
            self.view.show(new_sels[0])

    def goto_begin(self, sel: sublime.Region, extend: bool) -> sublime.Region:
        eos, bos = sel
        expanded = self.view.indented_region(bos)
        if expanded:
            pos = expanded.begin()
            if pos == self.view.line(bos).begin():
                expanded = self.view.indented_region(pos - 1)
                if expanded:
                    pos = expanded.begin()
                else:
                    pos = self.view.line(pos - 1).begin()

            # position caret to beginning of non-whitespace content
            pos = self.view.find(r"^\s*", pos).end()

        else:
            pos = 0

        if extend:
            return sublime.Region(eos, pos)
        else:
            return sublime.Region(pos)

    def goto_end(self, sel: sublime.Region, extend: bool) -> sublime.Region:
        eos, bos = sel
        expanded = self.view.indented_region(bos)
        if expanded:
            pos = expanded.end() - 1
            if pos == bos:
                expanded = self.view.indented_region(pos + 1)
                if expanded:
                    pos = expanded.end() - 1
                else:
                    pos = self.view.line(pos + 1).end()
        else:
            pos = self.view.size()

        if extend:
            return sublime.Region(eos, pos)
        else:
            return sublime.Region(pos)

    def goto_next(self, sel: sublime.Region, extend: bool) -> sublime.Region:
        eos, bos = sel
        bol, eol = prev = line = self.view.line(bos)
        col = bos - bol
        target_level = self.view.indentation_level(bos)
        block = False
        stop = False

        pos = eos
        eof = self.view.size()
        while eol < eof:
            bol, eol = line = self.view.line(eol + 1)

            if not line:
                stop = True
                continue

            level = self.view.indentation_level(bol)
            if level > target_level:
                if block:
                    pos = prev.begin() + min(col, len(prev) - 1)
                    break

                # find end of indented child block
                eol = self.view.indented_region(bol).end()
                stop = True
                continue

            text = self.view.substr(line)
            if text.isspace():
                stop = True
                continue

            if level < target_level:
                pos = prev.begin() + min(col, len(prev) - 1)
                break

            if stop:
                pos = bol + min(col, len(line) - 1)
                break

            prev = line
            block = True

        if extend:
            return sel if (eos == pos) and (eos < bos) else sublime.Region(eos, pos)
        else:
            return sublime.Region(pos)

    def goto_prev(self, sel: sublime.Region, extend: bool) -> sublime.Region:
        eos, bos = sel
        bol, eol = prev = line = self.view.line(bos)
        col = bos - bol
        target_level = self.view.indentation_level(bos)
        block = False
        stop = False

        pos = eos
        while bol > 0:
            bol, eol = line = self.view.line(bol - 1)
            if not line:
                stop = True
                continue

            level = self.view.indentation_level(bol)
            if level > target_level:
                if block:
                    pos = prev.begin() + min(col, len(prev) - 1)
                    break

                # find beginning of indented child block
                bol = self.view.indented_region(bol).begin()
                stop = True
                continue

            text = self.view.substr(line)
            if text.isspace():
                stop = True
                continue

            if level < target_level:
                pos = prev.begin() + min(col, len(prev) - 1)
                break

            if stop:
                pos = bol + min(col, len(line) - 1)
                break

            prev = line
            block = True

        if extend:
            return sel if (eos == pos) and (eos > bos) else sublime.Region(eos, pos)
        else:
            return sublime.Region(pos)
