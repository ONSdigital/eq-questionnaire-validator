from app.validators.blocks.block_validator import BlockValidator
from app.validators.blocks.calculated_summary_block_validator import (
    CalculatedSummaryBlockValidator,
)
from app.validators.blocks.list_collector_driving_question_validator import (
    ListCollectorDrivingQuestionValidator,
)
from app.validators.blocks.list_collector_validator import ListCollectorValidator
from app.validators.blocks.primary_person_list_collector_validator import (
    PrimaryPersonListCollectorValidator,
)
from app.validators.blocks.relationship_collector_validator import (
    RelationshipCollectorValidator,
)


def get_block_validator(block, questionnaire_schema):
    validators = {
        "CalculatedSummary": CalculatedSummaryBlockValidator,
        "PrimaryPersonListCollector": PrimaryPersonListCollectorValidator,
        "ListCollector": ListCollectorValidator,
        "ListCollectorDrivingQuestion": ListCollectorDrivingQuestionValidator,
        "RelationshipCollector": RelationshipCollectorValidator,
    }
    return validators.get(block["type"], BlockValidator)(block, questionnaire_schema)
