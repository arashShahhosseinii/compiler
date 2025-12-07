# <Arash shahhoseini, 402170979> <AmirHosein shayan, 402170981> 
# Scanner for C-minus

# Constants
KEYWORDS = {"break", "else", "for", "if", "int", "return", "void"}
SYMBOL_SINGLE = set([';', ':', ',', '[', ']', '(', ')', '{', '}', '+', '-', '*', '/', '=', '<'])
WHITESPACE = {' ', '\n', '\r', '\t', '\v', '\f'}

# --- Helper Functions ---

def is_letter(ch):
    """Checks if a character is a letter (a-z, A-Z)."""
    if not ch: return False
    return ch.isalpha()

def is_digit(ch):
    """Checks if a character is a digit (0-9)."""
    if not ch: return False
    return ch.isdigit()

def is_alnum(ch):
    """Checks if a character is alphanumeric or an underscore (valid in IDs)."""
    return is_letter(ch) or is_digit(ch) or ch == '_'

# --- Scanner Class ---

class Scanner:
    FINAL_SYMBOLS = {';', ':', ',', '[', ']', '(', ')', '{', '}', '+', '-'}

    def __init__(self, input_text):
        self.src = input_text
        self.current_pos = 0
        self.line_number = 1
        self.source_length = len(input_text)
        
        self.symbol_table = []
        self.symbol_set = set()
        
        # Initialize symbol table with sorted keywords
        for kw in sorted(KEYWORDS):
            self._register_symbol(kw)

        self.tokens_by_line = {}  
        self.lexical_errors = []

    def _register_symbol(self, lexeme):
        """Adds a new identifier to the symbol table if it doesn't already exist."""
        if lexeme not in self.symbol_set:
            self.symbol_table.append(lexeme)
            self.symbol_set.add(lexeme)

    def peek(self, k=1):
        """Returns the next k characters without advancing the position."""
        if self.current_pos >= self.source_length:
            return ''
        return self.src[self.current_pos:self.current_pos+k]

    def advance(self, n=1):
        """Consumes and returns the next n characters, updating position and line number."""
        chars = ''
        for _ in range(n):
            if self.current_pos >= self.source_length:
                return chars
            ch = self.src[self.current_pos]
            chars += ch
            self.current_pos += 1
            if ch == '\n':
                self.line_number += 1
        return chars

    def record_token(self, token_type, lexeme, line_no=None):
        """Records a successfully scanned token."""
        if line_no is None:
            line_no = self.line_number
        self.tokens_by_line.setdefault(line_no, []).append((token_type, lexeme))

    def record_error(self, thrown, message, line_no=None):
        """Records a lexical error."""
        if line_no is None:
            line_no = self.line_number
        self.lexical_errors.append((line_no, thrown, message))
        
    def get_next_token(self):
        """
        Main logic for the finite state machine of the scanner.
        """
        while True:
            start_lineno = self.line_number
            c = self.peek(1)
            
            if not c: return None

            # 1. Skip Whitespace
            if c in WHITESPACE:
                self.advance(1)
                continue
            
            # 2. Identifier / Keyword
            if is_letter(c) or c == '_':
                lexeme = self.advance(1)
                while is_alnum(self.peek(1)):
                    lexeme += self.advance(1)

                nxt = self.peek(1)
                
                # Panic Mode Recovery for ID/Keyword followed by Illegal character
                if nxt and not is_alnum(nxt) and nxt not in WHITESPACE and nxt not in SYMBOL_SINGLE:
                    bad_lexeme = lexeme
                    while True:
                        nxt_err = self.peek(1)
                        if not nxt_err or nxt_err in WHITESPACE:
                            break
                        if nxt_err in SYMBOL_SINGLE:
                            break 
                        bad_lexeme += self.advance(1)
                        
                    self.record_error(bad_lexeme, 'Illegal character', start_lineno)
                    continue
                
                if lexeme in KEYWORDS:
                    return ('KEYWORD', lexeme, start_lineno)
                else:
                    self._register_symbol(lexeme)
                    return ('ID', lexeme, start_lineno)

            # 3. Number
            if is_digit(c):
                lexeme = self.advance(1)
                while is_digit(self.peek(1)):
                    lexeme += self.advance(1)

                nxt = self.peek(1)
                
                # Malformed number (followed by letter or underscore) e.g., '123a'
                if nxt and (is_letter(nxt) or nxt == '_'):
                    bad = lexeme
                    while is_alnum(self.peek(1)):
                        bad += self.advance(1)
                    self.record_error(bad, 'Malformed number', start_lineno)
                    continue

                # Leading zero rule (e.g., '012')
                if len(lexeme) > 1 and lexeme[0] == '0':
                    self.record_error(lexeme, 'Malformed number', start_lineno)
                    continue

                # Panic Mode Recovery for NUM followed by Illegal character
                if nxt and not is_alnum(nxt) and nxt not in WHITESPACE and nxt not in SYMBOL_SINGLE:
                    bad_lexeme = lexeme
                    while True:
                        nxt_err = self.peek(1)
                        if not nxt_err or nxt_err in WHITESPACE:
                            break
                        if nxt_err in SYMBOL_SINGLE:
                            break
                            
                        bad_lexeme += self.advance(1)
                        
                    self.record_error(bad_lexeme, 'Illegal character', start_lineno)
                    continue
                    
                return ('NUM', lexeme, start_lineno)

            # 4. Slash -> comment or division symbol
            if c == '/':
                two = self.peek(2)
                if two == '//': # Single-line comment
                    self.advance(2)
                    while self.peek(1) not in ['\n', '\f', '']:
                        self.advance(1)
                    continue
                    
                elif two == '/*': # Multi-line comment
                    self.advance(2)
                    comment_content = ''
                    comment_start_line = start_lineno
                    
                    while True:
                        if not self.peek(1): 
                            # Open comment at EOF error
                            snippet = comment_content
                            if len(snippet) > 10: snippet = snippet[:10] + '...'
                            thrown = '/*' + snippet
                            self.record_error(thrown, 'Open comment at EOF', comment_start_line)
                            return None
                            
                        if self.peek(2) == '*/':
                            self.advance(2)
                            break
                            
                        ch = self.advance(1)
                        comment_content += ch
                        
                    continue
                    
                else:
                    self.advance(1)
                    return ('SYMBOL', '/', start_lineno)

            # 5. Equals or double equals
            if c == '=':
                if self.peek(2) == '==':
                    self.advance(2)
                    return ('SYMBOL', '==', start_lineno)
                else:
                    self.advance(1)
                    return ('SYMBOL', '=', start_lineno)

            # 6. Asterisk: multiplication or stray closing comment '*/'
            if c == '*':
                self.advance(1) 
                # Check for stray closing comment
                if self.peek(1) == '/':
                    self.advance(1)
                    self.record_error('*/', 'Stray closing comment', start_lineno)
                    continue
                else:
                    return ('SYMBOL', '*', start_lineno)

            # 7. Less-than
            if c == '<':
                self.advance(1)
                return ('SYMBOL', '<', start_lineno)

            # 8. Other single-char symbols (unambiguous)
            if c in Scanner.FINAL_SYMBOLS:
                self.advance(1)
                return ('SYMBOL', c, start_lineno)

            # 9. Illegal character at top-level
            bad = self.advance(1)
            # Panic Mode Recovery for single Illegal character
            while True:
                nxt = self.peek(1)
                if not nxt or nxt in WHITESPACE:
                    break
                if nxt in SYMBOL_SINGLE:
                    break
                bad += self.advance(1)
                
            self.record_error(bad, 'Illegal character', start_lineno)
            continue

    def run_all(self):
        """Iterates through the source text and generates all tokens and errors."""
        while True:
            tok = self.get_next_token()
            if tok is None:
                break
            token_type, lexeme, ln = tok
            self.record_token(token_type, lexeme, ln)

    def write_outputs(self):
        """Writes the generated tokens, errors, and symbol table to files."""
        # tokens.txt
        with open('tokens.txt', 'w', encoding='utf-8') as f:
            for ln in sorted(self.tokens_by_line.keys()):
                toks = self.tokens_by_line[ln]
                entries = ' '.join(f"({t[0]}, {t[1]})" for t in toks)
                f.write(f"{ln}.\t{entries}\n")

        # lexical_errors.txt
        with open('lexical_errors.txt', 'w', encoding='utf-8') as f:
            if not self.lexical_errors:
                f.write("No lexical errors found.\n")
            else:
                sorted_errors = sorted(self.lexical_errors, key=lambda x: x[0])
                for ln, thrown, msg in sorted_errors:
                    f.write(f"{ln}.\t({thrown}, {msg})\n")

        # symbol_table.txt: Keywords (sorted) then IDs (sorted)
        identifiers = [lex for lex in self.symbol_table if lex not in KEYWORDS]
        identifiers_unique_sorted = sorted(list(set(identifiers)))
        
        keywords_sorted = sorted(KEYWORDS)

        with open('symbol_table.txt', 'w', encoding='utf-8') as f:
            idx = 1
            # Keywords 
            for kw in keywords_sorted:
                f.write(f"{idx}.\t{kw}\n")
                idx += 1
            # Identifiers
            for ident in identifiers_unique_sorted:
                f.write(f"{idx}.\t{ident}\n")
                idx += 1


def main():
    try:
        with open('input.txt', 'r', encoding='utf-8') as f:
            src = f.read()
    except FileNotFoundError:
        print("Error: 'input.txt' not found. Please ensure the input file is in the same directory.")
        return

    scanner = Scanner(src)
    scanner.run_all()
    scanner.write_outputs()

if __name__ == '__main__':
    main()