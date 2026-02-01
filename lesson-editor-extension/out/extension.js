"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
function activate(context) {
    const insertSnippet = (snippet) => {
        const editor = vscode.window.activeTextEditor;
        if (!editor)
            return;
        editor.insertSnippet(new vscode.SnippetString(snippet));
    };
    // Commands
    context.subscriptions.push(vscode.commands.registerCommand("lesson.insertNote", () => {
        insertSnippet("/i ${1:note text} \\\n");
    }), vscode.commands.registerCommand("lesson.insertWarning", () => {
        insertSnippet("/w ${1:warning text} \\\n");
    }), vscode.commands.registerCommand("lesson.insertTip", () => {
        insertSnippet("/t ${1:tip text} \\\n");
    }), vscode.commands.registerCommand("lesson.wrapSpoiler", () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor)
            return;
        const selection = editor.selection;
        const text = editor.document.getText(selection);
        editor.edit(editBuilder => {
            editBuilder.replace(selection, `||${text}||`);
        });
    }));
    // Hover provider
    context.subscriptions.push(vscode.languages.registerHoverProvider("markdown", {
        provideHover(document, position) {
            const range = document.getWordRangeAtPosition(position, /\/[iwt]|::[a-zA-Z#0-9]+|~quizzes:[^~]+~|\|\|[^|]+\|\|/);
            if (!range)
                return;
            const word = document.getText(range);
            if (word.startsWith("/i"))
                return new vscode.Hover("Info note block (`/i ... \\`).");
            if (word.startsWith("/w"))
                return new vscode.Hover("Warning note block (`/w ... \\`).");
            if (word.startsWith("/t"))
                return new vscode.Hover("Tip note block (`/t ... \\`).");
            if (word.startsWith("::"))
                return new vscode.Hover("Color tag (`::color{...}`).");
            if (word.startsWith("~quizzes"))
                return new vscode.Hover("Quiz embed (`~quizzes:lesson:id~`).");
            if (word.startsWith("||"))
                return new vscode.Hover("Spoiler text (`||...||`).");
            return;
        }
    }));
    // Diagnostics (linting)
    const diagnosticCollection = vscode.languages.createDiagnosticCollection("lesson");
    context.subscriptions.push(diagnosticCollection);
    const lintDocument = (doc) => {
        if (doc.languageId !== "markdown")
            return;
        const diagnostics = [];
        const text = doc.getText();
        const lines = text.split(/\r?\n/);
        // 1. Notes must end with backslash
        lines.forEach((line, index) => {
            if (line.match(/^\/[iwt]\s+/) && !line.trim().endsWith("\\")) {
                diagnostics.push(new vscode.Diagnostic(new vscode.Range(index, 0, index, line.length), "Note lines (`/i`, `/w`, `/t`) should end with a backslash (`\\`).", vscode.DiagnosticSeverity.Warning));
            }
        });
        // 2. Spoilers must be closed
        const spoilerRegex = /\|\|/g;
        let spoilerCount = 0;
        let match;
        while ((match = spoilerRegex.exec(text)) !== null) {
            spoilerCount++;
        }
        if (spoilerCount % 2 !== 0) {
            diagnostics.push(new vscode.Diagnostic(new vscode.Range(0, 0, 0, 1), "Unbalanced spoiler markers (`||`). Make sure spoilers are properly closed.", vscode.DiagnosticSeverity.Warning));
        }
        // 3. Block markers ::: should be balanced
        const blockStart = text.match(/:::[a-zA-Z]+/g)?.length ?? 0;
        const blockEnd = text.match(/:::/g)?.length ?? 0;
        if (blockEnd < blockStart) {
            diagnostics.push(new vscode.Diagnostic(new vscode.Range(0, 0, 0, 1), "Unbalanced block markers (`:::`). Some blocks may be missing a closing `:::`.", vscode.DiagnosticSeverity.Warning));
        }
        diagnosticCollection.set(doc.uri, diagnostics);
    };
    context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(lintDocument), vscode.workspace.onDidChangeTextDocument(e => lintDocument(e.document)), vscode.workspace.onDidCloseTextDocument(doc => diagnosticCollection.delete(doc.uri)));
    // Run once on activation for the active document
    if (vscode.window.activeTextEditor) {
        lintDocument(vscode.window.activeTextEditor.document);
    }
    // Completion provider
    context.subscriptions.push(vscode.languages.registerCompletionItemProvider("markdown", {
        provideCompletionItems(document, position) {
            const completions = [];
            // Color tags
            const colors = ["blue", "red", "green"];
            for (const color of colors) {
                const item = new vscode.CompletionItem(`::${color}{}`, vscode.CompletionItemKind.Snippet);
                item.insertText = new vscode.SnippetString(`::${color}{\${1:text}}`);
                item.detail = `Lesson color tag (${color})`;
                completions.push(item);
            }
            // Block types
            const blockTypes = ["blockquote", "warning"];
            for (const block of blockTypes) {
                const item = new vscode.CompletionItem(`:::${block}`, vscode.CompletionItemKind.Snippet);
                item.insertText = new vscode.SnippetString(`:::${block} \${1:content} :::`);
                item.detail = `Lesson block (${block})`;
                completions.push(item);
            }
            // Quiz skeleton
            const quizItem = new vscode.CompletionItem("lesson quiz", vscode.CompletionItemKind.Snippet);
            quizItem.insertText = new vscode.SnippetString("~quizzes:${1:lesson}:${2:id}~");
            quizItem.detail = "Lesson quiz embed";
            completions.push(quizItem);
            return completions;
        }
    }, ":", "~", "/" // trigger characters
    ));
}
function deactivate() { }
//# sourceMappingURL=extension.js.map