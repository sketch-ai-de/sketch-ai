from sketch_ai_types import DocumentTypeRobotArm


class Metadata:
    def __init__(
        self, company_name: str, product_name: str, document_type: DocumentTypeRobotArm
    ):
        self.company_name = company_name
        self.product_name = product_name
        self.document_type = document_type

    def get_dict(self):
        return {
            "company_name": self.company_name,
            "product_name": self.product_name,
            "document_type": self.document_type,
        }
