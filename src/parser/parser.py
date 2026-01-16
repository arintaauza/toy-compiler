"""
Recursive descent parser for the Toy compiler.

The parser consumes tokens from the lexer and builds an Abstract Syntax Tree (AST).
It implements a recursive descent parser with precedence climbing for expressions.

Grammar (simplified):
    program        → declaration* EOF
    declaration    → funcDecl | varDecl | constDecl
    funcDecl       → "fn" IDENTIFIER "(" parameters? ")" "->" type block
    varDecl        → "let" IDENTIFIER ":" type ("=" expression)? ";"
    constDecl      → "const" IDENTIFIER ":" type "=" expression ";"
    statement      → exprStmt | block | ifStmt | whileStmt | returnStmt | varDecl
    block          → "{" statement* "}"
    ifStmt         → "if" expression block ("else" (ifStmt | block))?
    whileStmt      → "while" expression block
    returnStmt     → "return" expression? ";"
    exprStmt       → expression ";"

Expression precedence (lowest to highest):
    assignment     → IDENTIFIER "=" assignment | logicOr
    logicOr        → logicAnd ("||" logicAnd)*
    logicAnd       → equality ("&&" equality)*
    equality       → comparison (("==" | "!=") comparison)*
    comparison     → term (("<" | ">" | "<=" | ">=") term)*
    term           → factor (("+" | "-") factor)*
    factor         → unary (("*" | "/" | "%") unary)*
    unary          → ("!" | "-") unary | call
    call           → primary ("(" arguments? ")")*
    primary        → NUMBER | STRING | "true" | "false" | IDENTIFIER | "(" expression ")"
"""

from typing import List, Optional, Callable
from src.lexer.token import Token, TokenType
from src.parser.ast_nodes import (
    # Type annotation
    TypeAnnotation,
    type_from_string,
    # Expressions
    Expression,
    LiteralExpr,
    VariableExpr,
    BinaryExpr,
    UnaryExpr,
    GroupingExpr,
    CallExpr,
    AssignmentExpr,
    # Statements
    Statement,
    ExprStmt,
    VarDeclStmt,
    BlockStmt,
    IfStmt,
    WhileStmt,
    ReturnStmt,
    # Declarations
    Parameter,
    FunctionDecl,
    Program,
)
from src.utils.error import ParserError


class Parser:
    """
    Recursive descent parser for Toy.

    Converts a stream of tokens into an Abstract Syntax Tree (AST).
    """

    def __init__(self, tokens: List[Token]):
        """
        Initialize the parser with a list of tokens.

        Args:
            tokens: List of tokens from the lexer (must end with EOF token)
        """
        self.tokens = tokens
        self.current = 0
        self.errors: List[ParserError] = []

    def parse(self) -> Program:
        """
        Parse the token stream into a complete Program AST.

        Returns:
            Program node representing the entire source file

        Raises:
            ParserError: If any syntax errors were encountered
        """
        declarations = []

        while not self._is_at_end():
            decl = self._parse_declaration()
            if decl is not None:
                declarations.append(decl)

        # If there were any errors, raise the first one
        if self.errors:
            raise self.errors[0]

        return Program(
            declarations=declarations,
            line=1,
            column=1
        )

    # =========================================================================
    # Declaration Parsing
    # =========================================================================

    def _parse_declaration(self) -> Optional[Statement]:
        """
        Parse a top-level declaration (function, variable, or constant).

        Returns:
            A declaration node, or None if parsing failed with recovery
        """
        try:
            if self._check(TokenType.FN):
                return self._parse_function_declaration()
            if self._check(TokenType.LET):
                return self._parse_var_declaration()
            if self._check(TokenType.CONST):
                return self._parse_const_declaration()

            # At top level, we only expect declarations
            raise self._error(
                self._peek(),
                "Expected function or variable declaration"
            )
        except ParserError as e:
            # Record the error
            self.errors.append(e)
            # Synchronize and continue parsing to find more errors
            self._synchronize()
            return None

    def _parse_function_declaration(self) -> FunctionDecl:
        """
        Parse a function declaration.

        Grammar: "fn" IDENTIFIER "(" parameters? ")" "->" type block
        """
        fn_token = self._advance()  # Consume 'fn'

        # Function name
        name_token = self._consume(
            TokenType.IDENTIFIER,
            "Expected function name after 'fn'"
        )

        # Parameters
        self._consume(TokenType.LPAREN, "Expected '(' after function name")
        parameters = self._parse_parameters()
        self._consume(TokenType.RPAREN, "Expected ')' after parameters")

        # Return type
        self._consume(TokenType.ARROW, "Expected '->' before return type")
        return_type = self._parse_type("Expected return type")

        # Body
        body = self._parse_block()

        return FunctionDecl(
            name=name_token.value,
            parameters=parameters,
            return_type=return_type,
            body=body,
            line=fn_token.line,
            column=fn_token.column
        )

    def _parse_parameters(self) -> List[Parameter]:
        """
        Parse function parameters.

        Grammar: (IDENTIFIER ":" type ("," IDENTIFIER ":" type)*)?
        """
        parameters = []

        if not self._check(TokenType.RPAREN):
            # Parse first parameter
            parameters.append(self._parse_parameter())

            # Parse remaining parameters
            while self._match(TokenType.COMMA):
                parameters.append(self._parse_parameter())

        return parameters

    def _parse_parameter(self) -> Parameter:
        """Parse a single function parameter."""
        name_token = self._consume(
            TokenType.IDENTIFIER,
            "Expected parameter name"
        )
        self._consume(TokenType.COLON, "Expected ':' after parameter name")
        param_type = self._parse_type("Expected parameter type")

        return Parameter(
            name=name_token.value,
            type_annotation=param_type,
            line=name_token.line,
            column=name_token.column
        )

    def _parse_var_declaration(self) -> VarDeclStmt:
        """
        Parse a variable declaration.

        Grammar: "let" IDENTIFIER ":" type ("=" expression)? ";"
        """
        let_token = self._advance()  # Consume 'let'

        name_token = self._consume(
            TokenType.IDENTIFIER,
            "Expected variable name after 'let'"
        )

        self._consume(TokenType.COLON, "Expected ':' after variable name")
        var_type = self._parse_type("Expected variable type")

        # Optional initializer
        initializer = None
        if self._match(TokenType.EQUAL):
            initializer = self._parse_expression()

        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")

        return VarDeclStmt(
            name=name_token.value,
            type_annotation=var_type,
            initializer=initializer,
            is_const=False,
            line=let_token.line,
            column=let_token.column
        )

    def _parse_const_declaration(self) -> VarDeclStmt:
        """
        Parse a constant declaration.

        Grammar: "const" IDENTIFIER ":" type "=" expression ";"
        """
        const_token = self._advance()  # Consume 'const'

        name_token = self._consume(
            TokenType.IDENTIFIER,
            "Expected constant name after 'const'"
        )

        self._consume(TokenType.COLON, "Expected ':' after constant name")
        const_type = self._parse_type("Expected constant type")

        self._consume(TokenType.EQUAL, "Expected '=' after constant type (constants must be initialized)")
        initializer = self._parse_expression()

        self._consume(TokenType.SEMICOLON, "Expected ';' after constant declaration")

        return VarDeclStmt(
            name=name_token.value,
            type_annotation=const_type,
            initializer=initializer,
            is_const=True,
            line=const_token.line,
            column=const_token.column
        )

    def _parse_type(self, error_message: str) -> TypeAnnotation:
        """
        Parse a type annotation.

        Grammar: "int" | "float" | "bool" | "string" | "void"
        """
        type_tokens = {
            TokenType.INT: TypeAnnotation.INT,
            TokenType.FLOAT: TypeAnnotation.FLOAT,
            TokenType.BOOL: TypeAnnotation.BOOL,
            TokenType.STRING_TYPE: TypeAnnotation.STRING,
            TokenType.VOID: TypeAnnotation.VOID,
        }

        for token_type, annotation in type_tokens.items():
            if self._match(token_type):
                return annotation

        raise self._error(self._peek(), error_message)

    # =========================================================================
    # Statement Parsing
    # =========================================================================

    def _parse_statement(self) -> Statement:
        """
        Parse a statement.

        Grammar: exprStmt | block | ifStmt | whileStmt | returnStmt | varDecl
        """
        if self._check(TokenType.LBRACE):
            return self._parse_block()
        if self._check(TokenType.IF):
            return self._parse_if_statement()
        if self._check(TokenType.WHILE):
            return self._parse_while_statement()
        if self._check(TokenType.RETURN):
            return self._parse_return_statement()
        if self._check(TokenType.LET):
            return self._parse_var_declaration()
        if self._check(TokenType.CONST):
            return self._parse_const_declaration()

        return self._parse_expression_statement()

    def _parse_block(self) -> BlockStmt:
        """
        Parse a block of statements.

        Grammar: "{" statement* "}"
        """
        brace_token = self._consume(TokenType.LBRACE, "Expected '{'")

        statements = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            stmt = self._parse_statement()
            statements.append(stmt)

        self._consume(TokenType.RBRACE, "Expected '}' after block")

        return BlockStmt(
            statements=statements,
            line=brace_token.line,
            column=brace_token.column
        )

    def _parse_if_statement(self) -> IfStmt:
        """
        Parse an if statement.

        Grammar: "if" expression block ("else" (ifStmt | block))?
        """
        if_token = self._advance()  # Consume 'if'

        condition = self._parse_expression()
        then_branch = self._parse_block()

        else_branch = None
        if self._match(TokenType.ELSE):
            if self._check(TokenType.IF):
                # else if
                else_branch = self._parse_if_statement()
            else:
                # else block
                else_branch = self._parse_block()

        return IfStmt(
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
            line=if_token.line,
            column=if_token.column
        )

    def _parse_while_statement(self) -> WhileStmt:
        """
        Parse a while statement.

        Grammar: "while" expression block
        """
        while_token = self._advance()  # Consume 'while'

        condition = self._parse_expression()
        body = self._parse_block()

        return WhileStmt(
            condition=condition,
            body=body,
            line=while_token.line,
            column=while_token.column
        )

    def _parse_return_statement(self) -> ReturnStmt:
        """
        Parse a return statement.

        Grammar: "return" expression? ";"
        """
        return_token = self._advance()  # Consume 'return'

        value = None
        if not self._check(TokenType.SEMICOLON):
            value = self._parse_expression()

        self._consume(TokenType.SEMICOLON, "Expected ';' after return statement")

        return ReturnStmt(
            value=value,
            line=return_token.line,
            column=return_token.column
        )

    def _parse_expression_statement(self) -> ExprStmt:
        """
        Parse an expression statement.

        Grammar: expression ";"
        """
        expr = self._parse_expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression")

        return ExprStmt(
            expression=expr,
            line=expr.line,
            column=expr.column
        )

    # =========================================================================
    # Expression Parsing (Precedence Climbing)
    # =========================================================================

    def _parse_expression(self) -> Expression:
        """Parse an expression (entry point for expression parsing)."""
        return self._parse_assignment()

    def _parse_assignment(self) -> Expression:
        """
        Parse an assignment expression.

        Grammar: IDENTIFIER "=" assignment | logicOr
        """
        expr = self._parse_logic_or()

        if self._match(TokenType.EQUAL):
            equals_token = self._previous()
            value = self._parse_assignment()

            if isinstance(expr, VariableExpr):
                return AssignmentExpr(
                    name=expr.name,
                    value=value,
                    line=expr.line,
                    column=expr.column
                )

            raise self._error(
                equals_token,
                "Invalid assignment target"
            )

        return expr

    def _parse_logic_or(self) -> Expression:
        """
        Parse a logical OR expression.

        Grammar: logicAnd ("||" logicAnd)*
        """
        expr = self._parse_logic_and()

        while self._match(TokenType.OR_OR):
            operator = self._previous()
            right = self._parse_logic_and()
            expr = BinaryExpr(
                left=expr,
                operator="||",
                right=right,
                line=operator.line,
                column=operator.column
            )

        return expr

    def _parse_logic_and(self) -> Expression:
        """
        Parse a logical AND expression.

        Grammar: equality ("&&" equality)*
        """
        expr = self._parse_equality()

        while self._match(TokenType.AND_AND):
            operator = self._previous()
            right = self._parse_equality()
            expr = BinaryExpr(
                left=expr,
                operator="&&",
                right=right,
                line=operator.line,
                column=operator.column
            )

        return expr

    def _parse_equality(self) -> Expression:
        """
        Parse an equality expression.

        Grammar: comparison (("==" | "!=") comparison)*
        """
        expr = self._parse_comparison()

        while self._match(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            operator = self._previous()
            right = self._parse_comparison()
            expr = BinaryExpr(
                left=expr,
                operator=operator.lexeme,
                right=right,
                line=operator.line,
                column=operator.column
            )

        return expr

    def _parse_comparison(self) -> Expression:
        """
        Parse a comparison expression.

        Grammar: term (("<" | ">" | "<=" | ">=") term)*
        """
        expr = self._parse_term()

        while self._match(TokenType.LESS, TokenType.LESS_EQUAL,
                          TokenType.GREATER, TokenType.GREATER_EQUAL):
            operator = self._previous()
            right = self._parse_term()
            expr = BinaryExpr(
                left=expr,
                operator=operator.lexeme,
                right=right,
                line=operator.line,
                column=operator.column
            )

        return expr

    def _parse_term(self) -> Expression:
        """
        Parse an additive expression.

        Grammar: factor (("+" | "-") factor)*
        """
        expr = self._parse_factor()

        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous()
            right = self._parse_factor()
            expr = BinaryExpr(
                left=expr,
                operator=operator.lexeme,
                right=right,
                line=operator.line,
                column=operator.column
            )

        return expr

    def _parse_factor(self) -> Expression:
        """
        Parse a multiplicative expression.

        Grammar: unary (("*" | "/" | "%") unary)*
        """
        expr = self._parse_unary()

        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            operator = self._previous()
            right = self._parse_unary()
            expr = BinaryExpr(
                left=expr,
                operator=operator.lexeme,
                right=right,
                line=operator.line,
                column=operator.column
            )

        return expr

    def _parse_unary(self) -> Expression:
        """
        Parse a unary expression.

        Grammar: ("!" | "-") unary | call
        """
        if self._match(TokenType.BANG, TokenType.MINUS):
            operator = self._previous()
            operand = self._parse_unary()
            return UnaryExpr(
                operator=operator.lexeme,
                operand=operand,
                line=operator.line,
                column=operator.column
            )

        return self._parse_call()

    def _parse_call(self) -> Expression:
        """
        Parse a function call expression.

        Grammar: primary ("(" arguments? ")")*
        """
        expr = self._parse_primary()

        while True:
            if self._match(TokenType.LPAREN):
                expr = self._finish_call(expr)
            else:
                break

        return expr

    def _finish_call(self, callee: Expression) -> CallExpr:
        """Finish parsing a function call after '(' has been consumed."""
        arguments = []

        if not self._check(TokenType.RPAREN):
            # Parse first argument
            arguments.append(self._parse_expression())

            # Parse remaining arguments
            while self._match(TokenType.COMMA):
                if len(arguments) >= 255:
                    self._error(self._peek(), "Cannot have more than 255 arguments")
                arguments.append(self._parse_expression())

        self._consume(TokenType.RPAREN, "Expected ')' after arguments")

        # Get the function name from the callee
        if isinstance(callee, VariableExpr):
            return CallExpr(
                callee=callee.name,
                arguments=arguments,
                line=callee.line,
                column=callee.column
            )

        raise self._error(
            self._previous(),
            "Can only call functions"
        )

    def _parse_primary(self) -> Expression:
        """
        Parse a primary expression.

        Grammar: NUMBER | STRING | "true" | "false" | IDENTIFIER | "(" expression ")"
        """
        # Boolean literals
        if self._match(TokenType.TRUE):
            token = self._previous()
            return LiteralExpr(
                value=True,
                literal_type=TypeAnnotation.BOOL,
                line=token.line,
                column=token.column
            )

        if self._match(TokenType.FALSE):
            token = self._previous()
            return LiteralExpr(
                value=False,
                literal_type=TypeAnnotation.BOOL,
                line=token.line,
                column=token.column
            )

        # Number literal
        if self._match(TokenType.NUMBER):
            token = self._previous()
            value = token.value
            if isinstance(value, float):
                lit_type = TypeAnnotation.FLOAT
            else:
                lit_type = TypeAnnotation.INT
            return LiteralExpr(
                value=value,
                literal_type=lit_type,
                line=token.line,
                column=token.column
            )

        # String literal
        if self._match(TokenType.STRING):
            token = self._previous()
            return LiteralExpr(
                value=token.value,
                literal_type=TypeAnnotation.STRING,
                line=token.line,
                column=token.column
            )

        # Identifier
        if self._match(TokenType.IDENTIFIER):
            token = self._previous()
            return VariableExpr(
                name=token.value,
                line=token.line,
                column=token.column
            )

        # Grouped expression
        if self._match(TokenType.LPAREN):
            paren_token = self._previous()
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return GroupingExpr(
                expression=expr,
                line=paren_token.line,
                column=paren_token.column
            )

        raise self._error(self._peek(), "Expected expression")

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _match(self, *token_types: TokenType) -> bool:
        """
        Check if current token matches any of the given types.
        If so, consume the token and return True.
        """
        for token_type in token_types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        """Check if current token is of the given type (without consuming)."""
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _advance(self) -> Token:
        """Consume and return the current token."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        """Check if we've reached the end of the token stream."""
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        """Return the current token without consuming it."""
        return self.tokens[self.current]

    def _previous(self) -> Token:
        """Return the most recently consumed token."""
        return self.tokens[self.current - 1]

    def _consume(self, token_type: TokenType, message: str) -> Token:
        """
        Consume the current token if it matches the expected type.
        Otherwise, raise a parser error.
        """
        if self._check(token_type):
            return self._advance()

        raise self._error(self._peek(), message)

    def _error(self, token: Token, message: str) -> ParserError:
        """Create a parser error at the given token."""
        return ParserError(
            message=message,
            line=token.line,
            column=token.column,
            token_lexeme=token.lexeme
        )

    def _synchronize(self):
        """
        Synchronize the parser after an error.

        Discards tokens until we find a statement boundary,
        allowing the parser to continue and report more errors.
        """
        self._advance()

        while not self._is_at_end():
            # Stop at statement boundaries
            if self._previous().type == TokenType.SEMICOLON:
                return

            # Stop at declaration keywords
            if self._peek().type in {
                TokenType.FN,
                TokenType.LET,
                TokenType.CONST,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.RETURN,
            }:
                return

            self._advance()


# =============================================================================
# Convenience Functions
# =============================================================================

def parse(tokens: List[Token]) -> Program:
    """
    Parse a list of tokens into an AST.

    Args:
        tokens: List of tokens from the lexer

    Returns:
        Program AST node

    Raises:
        ParserError: If a syntax error is encountered
    """
    parser = Parser(tokens)
    return parser.parse()


def parse_source(source: str) -> Program:
    """
    Lex and parse Toy source code into an AST.

    Args:
        source: Toy source code as a string

    Returns:
        Program AST node

    Raises:
        LexerError: If a lexical error is encountered
        ParserError: If a syntax error is encountered
    """
    from src.lexer.lexer import tokenize
    tokens = tokenize(source)
    return parse(tokens)
