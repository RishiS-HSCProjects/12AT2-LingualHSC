---

title: Lingual Developers
summary: Want to create your own lessons (or languages)?? Found an issue with educated content? Start here!

---

Lingual HSC relies on volunteer lesson and quiz developers to run this free, open source resource.

Since our developers are mostly students, there exists a good chance that mistakes may have been made and missed during development. You have also have some suggestions to enhance the education of specific concepts more clearly.

Since this project is open source, anyone has the right to edit. However, there are a few conventions you will need to abide by to keep the Lingual experience streamlined.

# Markdown Syntax

Lingual Lessons supports all standard markdown syntaxes, so if you're familiar with markdown, you can use all of the standard formatting options to create your lessons.

Here are some of the most commonly used markdown syntaxes that you can use in your lessons.

| Syntax | Description |
| --- | --- |
| `#` | **Heading 1** |
| `##` | **Heading 2** |
| `###` | **Heading 3** |
| `*text*` | *Italic text* |
| `_text_` | _Italic text_ |
| `**text**` | **Bold text** |
| `__text__` | __Bold text__ |
| `-` | • Unordered list |
| `1.` | ➀ Ordered list |
| `>` | > Quote |
| `[text](url)` | [Link](https://www.youtube.com/watch?v=dQw4w9WgXcQ) |
| `![alt text](image_url)` | ![Image](fake image for symbol) |
| `---` | 一 Horizontal rule |
| `` `code` `` | `Inline code` |
| ```` ```code block``` ```` | ```Code block``` |

# Custom Blocks

/w Markdown syntaxes are not supported within custom blocks (including Lingual Quizzes data). To use rich text formatting within blocks, please use the respective HTML tags (e.g. ˂em˃Italic˂/em˃ becomes <em>Italic</em>) \

In addition to standard markdown syntaxes, Lingual Lessons also supports custom blocks that allow you to create interactive and engaging content for your lessons. Here are some of the custom blocks that you can use in your lessons.

:::subject ꞉꞉꞉type text ꞉꞉꞉ :::

Valid types include `blockquote`, `subject`, and `warning`.

:::blockquote blockquotes are used to highlight phrases or structures :::
:::subject subjects are used to emphasise important concepts :::
:::warning warnings are used to alert users to important information :::

:::subject ꞉꞉colour{text} :::

The colour can be any valid CSS colour, including hex codes, RGB values, or colour names. This syntax is used to change the colour of the text within the curly braces. For example, `꞉꞉red{This text is red}` will render like "::red{This text is red}". Or if you want more fancy colours, `꞉꞉#8D51AE{This is a nice, custom hybrid between light purple and pink}` becomes "::#8D51AE{This is a nice, custom hybrid between light purple and pink}".

/t All of the syntax definitions use subject blocks! \

:::subject [text](lessons꞉lesson-id#anchor) :::

This syntax is used to create internal links to other lessons within the Lingual HSC application. The `lesson-id` should correspond to the slug of the lesson you want to link to. For example, if you have a lesson with the slug `about-us`, you can link to it using *`[About Us](lessons꞉about-us)`*, which will render as [About Us](lessons:about-us). The text before the colon links to the lesson route.

You can also include an optional anchor after the lesson ID to link to a specific section within the lesson. For example, *`[About Us - Our Story](lessons꞉about-us#our-story)`* will link to the ["Our Story" section of the "About Us" lesson](lessons:about-us#our-story).

:::subject ¦¦ spoiler text ¦¦ :::

Pipes are used to create spoiler blocks that hide the text within them. Users can click on the block to reveal the hidden text. For example, `¦¦ This is a spoiler ¦¦` will render "||This is a spoiler||". When clicked, it will reveal the hidden text.

Spoiler blocks are useful for ||hiding answers|| to general knowledge questions, or ||giving hints|| for questions without giving away the full answer. You can also use them to ||hide additional information|| that might be useful for users who want to learn more, without overwhelming those who just want to focus on the basics.


:::subject ⁓quizzes:[lesson]:[id]⁓ :::

*[lesson]* corresponds to the name of the .json file (usually the lesson) where the quiz is located.

*[id]* corresponds to the quiz ID within the file.

Because of this setup, you can also query quiz from other lessons within your module!

For a test of how quizzes look like, [click here](lessons:getting-started#quizzes)!

/t You can use custom blocks within quizzes! \
