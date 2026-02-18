---

title: Getting Started with Lingual HSC
summary: An introduction to the Lingual HSC tutorial module, guiding users through the features and functionalities of the application.

---

:::blockquote Want to know more about Lingual HSC? [Click here](lessons:about-us)! :::

# Welcome to Lingual Lessons!

This is the tutorial module of Lingual HSC where you can understand how we do things around here!

All languages have Lingual Lessons integration. This is how all of the lessons in Lingual HSC look like!

Lingual Lessons is a markdown-based lesson format that allows us to create interactive and engaging lessons for our users. It supports a wide range of features, including quizzes, blocks, and various formatting options to make the learning experience more enjoyable and effective, along with custom language-specific syntaxes to make it easier for us to create content that is relevant to the language being taught.

This page doubles as a tutorial for how to create your own lessons using Lingual Lessons, so if you're interested in contributing to the content of Lingual HSC, this is a good place to start!

# Markdown Syntax

:::::warning **Not a developer? Click this →** ||Skip to the [Spoiler Blocks](lessons:getting-started#spoiler-text) Section|| :::

Lingual Lessons supports all standard markdown syntaxes, so if you're familiar with markdown, you can use all of the standard formatting options to create your lessons.

Here are some of the most commonly used markdown syntaxes that you can use in your lessons.

| Syntax | Description |
| --- | --- |
| `#` | Heading 1 |
| `##` | Heading 2 |
| `###` | Heading 3 |
| `*text*` | Italic text |
| `_text_` | Italic text |
| `**text**` | Bold text |
| `__text__` | Bold text |
| `-` | Unordered list |
| `1.` | Ordered list |
| `>` | Quote |
| `[text](url)` | Link |
| `![alt text](image_url)` | Image |
| `---` | Horizontal rule |
| `` `code` `` | Inline code |
| ```` ```code block``` ```` | Code block |

# Custom Blocks
In addition to standard markdown syntaxes, Lingual Lessons also supports custom blocks that allow you to create interactive and engaging content for your lessons. Here are some of the custom blocks that you can use in your lessons.

## ```꞉꞉꞉type text ꞉꞉꞉```
Valid types include `blockquote`, `subject`, and `warning`.

:::blockquote blockquotes are used to highlight phrases or structures :::
:::subject subjects are used to emphasise important concepts :::
:::warning warnings are used to alert users to important information :::

## ```꞉꞉colour{text}```
The colour can be any valid CSS colour, including hex codes, RGB values, or colour names. This syntax is used to change the colour of the text within the curly braces. For example, `꞉꞉red{This text is red}` will render like ::red{This text is red}.

## ```[text](lessons꞉lesson-id#anchor)```

This syntax is used to create internal links to other lessons within the Lingual HSC application. The `lesson-id` should correspond to the slug of the lesson you want to link to. For example, if you have a lesson with the slug `about-us`, you can link to it using *`[About Us](lessons꞉about-us)`*, which will render as [About Us](lessons:about-us). The text before the colon links to the lesson route.

You can also include an optional anchor after the lesson ID to link to a specific section within the lesson. For example, *`[About Us - Our Story](lessons꞉about-us#our-story)`* will link to the ["Our Story" section of the "About Us" lesson](lessons:about-us#our-story).

## ```¦¦ spoiler text ¦¦```

Pipes are used to create spoiler blocks that hide the text within them. Users can click on the block to reveal the hidden text. For example, `¦¦ This is a spoiler ¦¦` will render as a clickable block that says "This is a spoiler". When clicked, it will reveal the hidden text.

Spoiler blocks are useful for ||hiding answers|| to general knowledge questions, or ||giving hints|| for questions without giving away the full answer. You can also use them to ||hide additional information|| that might be useful for users who want to learn more, without overwhelming those who just want to focus on the basics.

# Quizzes

Lingual Lessons also supports quizzes that allow you to create interactive questions for your users. You can create multiple choice questions, fill in the blank questions, and more. Quizzes are a great way to test your users' understanding of the material and provide them with immediate feedback.

Here, try out this quiz!

~quizzes:getting-started:intro~

**To get started, [click here](/register)!**
