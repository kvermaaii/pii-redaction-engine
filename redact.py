import sys
from docx import Document
from faker import Faker
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

def setup_engines():
    """Initializes the Presidio Analyzer, Anonymizer, and Faker."""
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
    
    anonymizer = AnonymizerEngine()
    fake = Faker()

    operators = {
        "PERSON": OperatorConfig("custom", {"lambda": lambda x: fake.name()}),
        "EMAIL_ADDRESS": OperatorConfig("custom", {"lambda": lambda x: fake.email()}),
        "PHONE_NUMBER": OperatorConfig("custom", {"lambda": lambda x: fake.phone_number()}),
        "ORGANIZATION": OperatorConfig("custom", {"lambda": lambda x: fake.company()}),
        "LOCATION": OperatorConfig("custom", {"lambda": lambda x: fake.address().replace('\n', ', ')}),
        "US_SSN": OperatorConfig("custom", {"lambda": lambda x: fake.ssn()}),
        "CREDIT_CARD": OperatorConfig("custom", {"lambda": lambda x: fake.credit_card_number()}),
        "DATE_TIME": OperatorConfig("custom", {"lambda": lambda x: fake.date_of_birth().strftime('%Y-%m-%d')}), 
        "IP_ADDRESS": OperatorConfig("custom", {"lambda": lambda x: fake.ipv4()})
    }
    
    return analyzer, anonymizer, operators

def redact_text(text: str, analyzer, anonymizer, operators) -> str:
    """Detects and redacts PII in a given string."""
    if not text.strip():
        return text
    
    entities = list(operators.keys())
    results = analyzer.analyze(text=text, entities=entities, language='en')
    
    if not results:
        return text
        
    anonymized_result = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=operators
    )
    return anonymized_result.text

def process_docx(input_path: str, output_path: str):
    """Reads a docx file, redacts PII from all paragraphs and tables, and saves it."""
    analyzer, anonymizer, operators = setup_engines()
    doc = Document(input_path)
    
    for para in doc.paragraphs:
        if para.text.strip():
            para.text = redact_text(para.text, analyzer, anonymizer, operators)
            
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    if para.text.strip():
                        para.text = redact_text(para.text, analyzer, anonymizer, operators)
                        
    doc.save(output_path)

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "Red Herring Prospectus.docx"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "Redacted_Output.docx"
    process_docx(input_file, output_file)
