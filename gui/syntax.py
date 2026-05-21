from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import re


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.rules = []

        kw_format = QTextCharFormat()
        kw_format.setForeground(QColor("#cba6f7"))
        kw_format.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "def", "class", "if", "elif", "else", "for", "while", "try",
            "except", "finally", "with", "as", "import", "from", "return",
            "yield", "raise", "break", "continue", "pass", "in", "not",
            "and", "or", "is", "None", "True", "False", "self", "async",
            "await", "lambda", "global", "nonlocal", "del", "assert"
        ]
        for kw in keywords:
            self.rules.append((re.compile(r'\b' + kw + r'\b'), kw_format))

        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#89b4fa"))
        builtins = ["print", "len", "range", "int", "str", "float", "list",
                    "dict", "set", "tuple", "type", "open", "input", "super",
                    "isinstance", "enumerate", "zip", "map", "filter", "sorted",
                    "reversed", "any", "all", "sum", "min", "max", "abs", "round"]
        for b in builtins:
            self.rules.append((re.compile(r'\b' + b + r'\b'), builtin_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#a6e3a1"))
        self.rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6c7086"))
        comment_format.setFontItalic(True)
        self.rules.append((re.compile(r'#.*$'), comment_format))

        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#f5c2e7"))
        self.rules.append((re.compile(r'@\w+'), decorator_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#fab387"))
        self.rules.append((re.compile(r'\b[0-9]+\b'), number_format))

        self.triple_rule = (re.compile(r'(""".*?"""|\'\'\'.*?\'\'\')', re.DOTALL), string_format)

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()
                self.setFormat(start, end - start, fmt)

        for match in self.triple_rule[0].finditer(text):
            start, end = match.start(), match.end()
            self.setFormat(start, end - start, self.triple_rule[1])


class PowerShellHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.rules = []

        cmdlet_format = QTextCharFormat()
        cmdlet_format.setForeground(QColor("#89b4fa"))
        cmdlets = [
            "Get-", "Set-", "Remove-", "New-", "Invoke-", "Write-",
            "Read-", "Start-", "Stop-", "Restart-", "Clear-", "Copy-",
            "Move-", "Rename-", "Select-", "Where-", "ForEach-", "Sort-",
            "Group-", "Measure-", "Compare-", "Out-", "Export-", "Import-",
            "ConvertTo-", "ConvertFrom-", "Format-", "Add-", "Update-"
        ]
        for c in cmdlets:
            self.rules.append((re.compile(r'\b' + c + r'\w+'), cmdlet_format))

        kw_format = QTextCharFormat()
        kw_format.setForeground(QColor("#cba6f7"))
        kw_format.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "if", "else", "elseif", "for", "foreach", "while", "do",
            "switch", "try", "catch", "finally", "return", "break",
            "continue", "exit", "throw", "function", "filter", "param",
            "begin", "process", "end", "dynamicparam", "in", "not",
            "and", "or", "eq", "ne", "gt", "lt", "ge", "le", "like",
            "match", "contains", "replace", "TRUE", "FALSE", "$true", "$false",
            "$null"
        ]
        for kw in keywords:
            self.rules.append((re.compile(r'\b' + kw + r'\b', re.IGNORECASE), kw_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#a6e3a1"))
        self.rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6c7086"))
        comment_format.setFontItalic(True)
        self.rules.append((re.compile(r'#.*$'), comment_format))
        self.rules.append((re.compile(r'<#[\s\S]*?#>'), comment_format))

        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor("#fab387"))
        self.rules.append((re.compile(r'\$\w+'), variable_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()
                self.setFormat(start, end - start, fmt)
