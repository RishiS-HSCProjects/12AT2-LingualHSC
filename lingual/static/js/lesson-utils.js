class DirectoryPanel {
    constructor({
        containerId = 'directory-results',
        contentSelector = '.lesson-content',
        offset = 120
    } = {}) {
        this.container = document.getElementById(containerId);
        this.content = document.querySelector(contentSelector);
        this.offset = offset;
        this.headings = [];

        if (!this.container || !this.content) return;

        this.init();
    }

    init() {
        this.extractHeadings();
        if (!this.headings.length) return;

        this.render();
        window.addEventListener('scroll', () => this.updateActive());
        this.updateActive();
    }

    extractHeadings() {
        const nodes = this.content.querySelectorAll('h1,h2,h3,h4,h5,h6');
        this.headings = [...nodes].map((h, i) => {
            h.id ||= `heading-${i}`;
            return {
                id: h.id,
                text: h.textContent.trim(),
                level: Number(h.tagName[1]),
                element: h
            };
        });
    }

    render() {
        this.container.innerHTML = this.headings.map(h => `
            <div class="directory-indent level-${h.level}" data-id="${h.id}">
                <a href="#${h.id}" class="directory-link">${h.text}</a>
            </div>
        `).join('');

        this.container.querySelectorAll('.directory-link').forEach(link => {
            link.addEventListener('click', e => {
                e.preventDefault();
                const id = link.getAttribute('href').slice(1);
                const target = document.getElementById(id);
                if (!target) return;

                window.scrollTo({
                    top: target.offsetTop - this.offset,
                    behavior: 'smooth'
                });
            });
        });
    }

    updateActive() {
        const pos = window.scrollY + this.offset + 1;
        let active = null;

        for (const h of this.headings) {
            if (pos >= h.element.offsetTop) active = h.id;
        }

        this.container.querySelectorAll('.directory-indent').forEach(el => {
            el.classList.toggle('active', el.dataset.id === active);
        });
    }
}

class QuizRenderer {
    constructor({
        quizSelector = '.quiz',
        questionClass = 'quiz-question',
        optionClass = 'quiz-option',
        correctClass = 'quiz-correct',
        incorrectClass = 'quiz-incorrect',
        lockDelay = 500 // ms
    } = {}) {
        this.quizSelector = quizSelector;
        this.questionClass = questionClass;
        this.optionClass = optionClass;
        this.correctClass = correctClass;
        this.incorrectClass = incorrectClass;
        this.lockDelay = lockDelay;

        this.init();
    }

    init() {
        document.querySelectorAll(this.quizSelector)
            .forEach(container => this.loadQuiz(container));
    }

    /* ----------------------------- */
    /* Loading State                 */
    /* ----------------------------- */

    renderLoading(container) {
        container.innerHTML = `
            <div class="quiz-loading">
                <div class="quiz-title">Loading Quiz</div>
                <div class="quiz-subtitle">Please wait…</div>
            </div>
        `;
    }

    /* ----------------------------- */
    /* Fetch                         */
    /* ----------------------------- */

    async loadQuiz(container) {
        const { lesson, id: quizId } = container.dataset;
        if (!lesson || !quizId) return;

        this.renderLoading(container);

        try {
            
            const res = await fetch(`/nihongo/api/quiz/${lesson}`);
            if (!res.ok) throw new Error('Quiz fetch failed');

            const data = await res.json();
            const quiz = data[quizId];
            if (!quiz || !quiz.bank?.length) throw new Error('Quiz data not found');

            this.startQuiz(container, quiz);
        } catch (err) {
            console.error('Quiz load error:', err);
            container.innerHTML = `
                <div class="quiz-error">
                    <div class="quiz-title">Error Loading Quiz</div>
                    <div class="quiz-subtitle">Please try again later.</div>
                </div>
            `;
        }
    }

    /* ----------------------------- */
    /* Quiz Start                    */
    /* ----------------------------- */

    startQuiz(container, quiz) {
        let questions = [...quiz.bank];

        if (quiz.random) {
            for (let i = questions.length - 1; i > 0; i--) {
                const j = Math.random() * (i + 1) | 0;
                [questions[i], questions[j]] = [questions[j], questions[i]];
            }
        }

        if (quiz.limit) {
            questions = questions.slice(0, quiz.limit);
        }

        this.renderQuestion(container, quiz, questions, 0, {
            correct: 0,
            total: questions.length
        });
    }

    /* ----------------------------- */
    /* Question Render               */
    /* ----------------------------- */

    renderQuestion(container, quiz, questions, index, score) {
        const q = questions[index];
        if (!q) return;

        container.innerHTML = `
            <div class="quiz-title">${quiz.title ?? 'Quiz'}</div>

            <div class="${this.questionClass}">
                ${q.question}
            </div>

            <ul class="quiz-options">
                ${q.options.map((opt, i) => `
                    <li class="${this.optionClass}" data-index="${i}">
                        ${opt}
                    </li>
                `).join('')}
            </ul>

            <div class="quiz-controls">
                <span class="quiz-progress">${index + 1} / ${questions.length}</span>
                <div class="quiz-next-container">
                    <button class="quiz-next-btn" disabled>
                        ${index + 1 < questions.length ? 'Next' : 'Finish'}
                    </button>
                </div>
            </div>
        `;

        const options = container.querySelectorAll(`.${this.optionClass}`);
        const nextBtn = container.querySelector('.quiz-next-btn');

        let answered = false;
        let locked = true;

        /* Misclick lock */
        setTimeout(() => locked = false, this.lockDelay);

        options.forEach(opt => {
            opt.addEventListener('click', () => {
                if (locked || answered) return;
                answered = true;

                const chosen = Number(opt.dataset.index);

                options.forEach((o, i) => {
                    o.style.pointerEvents = 'none';
                    if (i === q.answer) o.classList.add(this.correctClass);
                    if (i === chosen && i !== q.answer)
                        o.classList.add(this.incorrectClass);
                });

                if (chosen === q.answer) score.correct++;

                nextBtn.disabled = false;
            });
        });

        nextBtn.addEventListener('click', () => {
            if (index + 1 < questions.length) {
                this.renderQuestion(container, quiz, questions, index + 1, score);
            } else {
                this.renderSummary(container, quiz, score);
            }
        });
    }

    /* ----------------------------- */
    /* Summary                       */
    /* ----------------------------- */

    renderSummary(container, quiz, score) {
        const percent = Math.round((score.correct / score.total) * 100);

        let header, subtitle;

        if (percent === 100) {
            header = "Perfect Score!";
            subtitle = "You're a natural!";
        } else if (percent >= 85) {
            header = "That's an A!";
            subtitle = "It seems you know your stuff!";
        } else if (percent >= 70) {
            header = "Good Effort!";
            subtitle = "A little more practice and you'll get there!";
        } else if (percent >= 50) {
            header = "Keep Trying!";
            subtitle = "Don't give up, practice makes perfect!";
        } else {
            header = "Needs Improvement!";
            subtitle = "Consider reviewing the material and trying again!";
        }

        container.innerHTML = `
            <div class="quiz-summary">
                <div class="quiz-header-container">
                    <p class="quiz-header">${header}</p>
                    <subtitle class="quiz-subtitle">${subtitle}</subtitle>
                </div>

                <div class="quiz-score">
                    ${score.correct} / ${score.total} (${percent}%) Correct
                </div>

                <div class="quiz-restart-container">
                    <button class="quiz-restart-btn">Retry Quiz</button>
                </div>
            </div>
        `;

        container.querySelector('.quiz-restart-btn')
            .addEventListener('click', () => {
                this.startQuiz(container, quiz);
            });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new DirectoryPanel();
    new QuizRenderer();
});
