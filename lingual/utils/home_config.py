class HomeConfig:
    def __init__(self) -> None:
        self.build: list["HomeSection | None"] = []

    def register_section(self, section: "HomeSection"):
        """ Registers section to config in order of registration. """
        self.build.append(section)

    def get_build(self) -> list["HomeSection | None"]:
        return self.build

    def add_separator(self):
        self.build.append(None) # type: ignore -> None elements become separators.

class HomeSection:
    def __init__(
        self,
        title: str = '',
    ) -> None:
        self.title: str = title
        self.items: list["HomeItem"] = []
    
    def add_items(self, *items: "HomeItem"):
        for item in items:
            if not isinstance(item, HomeItem):
                raise HomeConfigException("Attempted to add item of type " + str(type(item)) + ". home_config::HomeItem expected.")
        
        self.items.extend([*items])

class HomeBanner (HomeSection):
    
    def __init__(self, content: str = "") -> None:
        super().__init__()
        self.content: str = content

class HomeItem :
    def __init__(self) -> None:
        self.classes: str = "" # Custom CSS classes to add to the item container.
        self.disabled = False # Not disabled (no reason given)

    def add_classes(self, *classes: str) -> "HomeItem":
        self.classes += " " + " ".join(classes)
        return self

    def set_disabled(self, reason: None|str = None, flash_category: str = "info"):
        """ Disables item interactions """
        self.add_classes('disabled')
        if reason: self.disabled = (reason, flash_category) # Set disabled reason

class ItemParagraph (HomeItem):
    """ Paragraph element. (Can not be disabled) """
    content = ""

    def __init__(
        self,
        content: str = ''
    ) -> None:
        super().__init__()
        self.content = content

class ItemBox(HomeItem):
    def __init__(
        self,
        title: str,
        body: str,
        buttons: None | list["ItemBox.BoxButton"] = None,
        on_click: str = None, # type: ignore -> URL to open when box is clicked.
        disabled_reason: str|None = None,
        disabled_flash_category: str|None = None
    ) -> None:
        super().__init__()
        self.title = title
        self.body = body
        self.buttons: list["ItemBox.BoxButton"] = list(buttons) if buttons else []
        if disabled_reason:
            if disabled_flash_category:
                self.set_disabled(disabled_reason, disabled_flash_category)
            else:
                self.set_disabled(disabled_reason)
            self.on_click = None
        else:
            self.on_click = on_click

        if not disabled_reason and on_click: self.add_classes("clickable")

    class BoxButton:
        def __init__(self, text: str, link: str) -> None:
            self.text = text
            self.link = link

    def add_buttons(self, buttons: list["BoxButton"]) -> "ItemBox":
        for button in buttons:
            if not isinstance(button, self.BoxButton):
                raise HomeConfigException(
                    f"Attempted to add button of type {type(button)}. home_config::ItemBox::BoxButton expected."
                )
        self.buttons.extend(buttons)
        return self

class HomeConfigException (Exception):
    """ Exception called during home config setup. """
    def __init__(self, *args: object) -> None:
        super().__init__(*args)