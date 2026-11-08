
"""Графічний інтерфейс перевірки початкових І / И."""

import html
import os
import gradio as gr

from spelling_checker import MAX_TEXT_LENGTH, analyze_text


CSS = """
.gradio-container {
    max-width: 1100px !important;
}

.hero {
    background: linear-gradient(125deg, #183d35, #326759);
    color: white;
    padding: 26px;
    border-radius: 18px;
    margin-bottom: 10px;
}

.hero h1 {
    color: white !important;
    font-size: 35px;
    margin: 0 0 6px;
}

.hero p {
    color: #ebf7f1;
    margin: 0;
}

.result {
    background: #fbfaf7;
    border: 1px solid #dddcd4;
    border-radius: 12px;
    padding: 17px;
    min-height: 130px;
    white-space: pre-wrap;
    line-height: 2;
    overflow-wrap: anywhere;
}

.mark-review {
    background: #ffe2a3;
    border-bottom: 2px solid #ca8a04;
    padding: 2px 3px;
    border-radius: 4px;
}

.mark-exception {
    background: #cfe5ff;
    padding: 2px 3px;
    border-radius: 4px;
}

.mark-variant {
    background: #d8eedc;
    padding: 2px 3px;
    border-radius: 4px;
}

.error {
    color: #992f2f;
    padding: 12px;
    background: #fff0ee;
    border: 1px solid #f0b9b2;
    border-radius: 10px;
}
"""


def highlight_text(result):
    """Створення HTML із підсвіченими словами."""

    styles = {
        "normal": "",
        "exception": "mark-exception",
        "variant": "mark-variant",
        "review": "mark-review",
    }

    fragments = []
    cursor = 0

    for finding in result.findings:
        fragments.append(
            html.escape(
                result.original_text[cursor:finding.start]
            )
        )

        word = html.escape(finding.word)
        style = styles[finding.status]

        if style:
            hint = html.escape(
                finding.explanation, quote=True
            )

            fragments.append(
                f'<span class="{style}" title="{hint}">'
                f'{word}</span>'
            )
        else:
            fragments.append(word)

        cursor = finding.end

    fragments.append(
        html.escape(result.original_text[cursor:])
    )

    return (
        '<div class="result">'
        + "".join(fragments)
        + '</div>'
    )


def check_text(text):
    """Передавання тексту до алгоритму та виведення результату."""

    try:
        result = analyze_text(text)

    except ValueError as error:
        message = html.escape(str(error))

        return (
            f'<div class="error">⚠️ {message}</div>',
            [],
            "",
            "**Перевірку не виконано.** "
            "Виправте введений текст.",
        )

    rows = [
        [
            item.word,
            item.label,
            item.suggestion,
            item.explanation
        ]
        for item in result.findings
    ]

    counts = result.counts

    summary = (
        f"**Усього слів:** {result.total_words} · "
        f"**Слів на і/и:** {len(result.findings)} · "
        f"**Можливих помилок:** {counts['review']} · "
        f"**Винятків:** {counts['exception']} · "
        f"**Варіантів:** {counts['variant']}"
    )

    if not result.findings:
        summary += (
            "\n\n*Слів на початкові «і» "
            "та «и» не знайдено.*"
        )

    return (
        highlight_text(result),
        rows,
        result.suggested_text,
        summary
    )


EXAMPLES = [
    ["Иван побачив индика, а поруч стояла Ірина."],
    ["Ич! Дитина почала икати, а в небі був ирій."],
    ["Ірій та ирій — нормативні варіанти написання."],
    ["Ірина читає історію про індика."],
]


with gr.Blocks(
    title="І чи И? — правописний аналізатор"
) as demo:

    gr.HTML("""
        <div class="hero">
            <h1>І чи И?</h1>
            <p>Навчальний правописний аналізатор
            української мови</p>
        </div>
    """)

    gr.Markdown(
        "Програма знаходить слова з початковими **і/и**, "
        "розрізняє винятки та варіантні написання "
        "й пропонує перевірити сумнівні слова."
    )

    with gr.Row():

        with gr.Column():

            source = gr.Textbox(
                label="Текст українською мовою",
                placeholder="Наприклад: Иван побачив индика...",
                lines=9,
                info=(
                    f"Введіть текст кирилицею, "
                    f"не більш як {MAX_TEXT_LENGTH} символів."
                ),
            )

            button = gr.Button(
                "Перевірити текст",
                variant="primary"
            )

            gr.Examples(
                EXAMPLES,
                inputs=source,
                label="Спробувати приклад"
            )

        with gr.Column():

            summary = gr.Markdown(
                "Тут з’явиться статистика аналізу."
            )

            gr.Markdown("### Текст із підсвічуванням")

            highlighted = gr.HTML(
                '<div class="result">'
                'Результат з’явиться тут.'
                '</div>'
            )

            gr.Markdown(
                "🟡 **Можлива помилка** · "
                "🔵 **Виняток** · "
                "🟢 **Варіант**"
            )

    table = gr.Dataframe(
        headers=[
            "Слово",
            "Статус",
            "Пропозиція",
            "Пояснення"
        ],
        datatype=["str", "str", "str", "str"],
        interactive=False,
        wrap=True,
        label="Детальний аналіз",
    )

    corrected = gr.Textbox(
        label="Текст із запропонованими виправленнями",
        lines=5,
        interactive=False,
        info=(
            "Пропозиції необхідно перевіряти: "
            "це навчальний правиловий алгоритм, "
            "а не повний словник."
        ),
    )

    button.click(
        fn=check_text,
        inputs=source,
        outputs=[
            highlighted,
            table,
            corrected,
            summary
        ],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", "7860")),
        inbrowser=False,
        theme=gr.themes.Soft(
            primary_hue="green",
            secondary_hue="amber"
        ),
        css=CSS
    )