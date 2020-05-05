from app.validation.validator import Validator


class BlockValidator(Validator):
    def __init__(self, block_element):
        super().__init__(block_element)
        self.block = block_element
        self.context["block_id"] = self.block["id"]
