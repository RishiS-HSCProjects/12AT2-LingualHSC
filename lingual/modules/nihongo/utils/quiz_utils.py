from lingual.utils import quiz_manager

class NihongoQuizTypes(quiz_manager.TypeEnum):
    GRAMMAR = quiz_manager.auto()
    KANJI = quiz_manager.auto()

    @property
    def description(self) -> str:
        descriptions = {
            self.GRAMMAR: "Collate quizzes on HSC Japanese grammar points, customisable by your preference!",
            self.KANJI: "Quizzes on kanji characters, including readings and meanings! Mastering kanji will start to remove the furigana from the grammar lessons and quizzes!"        }
        return descriptions.get(self, "")
