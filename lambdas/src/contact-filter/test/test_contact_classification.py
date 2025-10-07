from chain.contact_classification import contact_classification_chain
from model.contact_classification import ContactClassification, ContactCategory


def test_can_classify_spam():
    SPAM_MESSAGE = """
    Hi,
    
    Your business now has the opportunity to eliminate thousands in credit card processing fees.
    
    We’ve helped countless clients save money on processing fees, including restaurants, HVAC, veterinary practices, auto repair shops, and more.
    
    Like most businesses, these companies rely on customers who pay with credit and debit cards. First MCS Payment Solutions is happy to provide a comprehensive payment processing solution that eliminates processing fees and increases revenue.
    
    May I give you more information?
    
    Thank you for your time,
    
    William Sutton
    (630) 349-2809
    william@firstmcspayments.com
    3755 E Main St. Ste 115, St Charles, IL 60174
    
    Respond with stop to optout."""
    classification_result: ContactClassification = contact_classification_chain.invoke(
        {"contact_message": SPAM_MESSAGE})

    print(classification_result)

    assert classification_result.contact_category == ContactCategory.SPAM
    assert classification_result.confidence_score >= 0.9

def test_can_classify_consulting_inquiry():
    CONSULTING_REQUEST = """
    Hello,
    
    We noticed your website, and think that your AI/ML skills would be helpful for an upcoming project we have.
    
    If you have any availability to consult for a paid project, please let us know.
    """
    classification_result: ContactClassification = contact_classification_chain.invoke(
        {"contact_message": CONSULTING_REQUEST})

    print(classification_result)

    assert classification_result.contact_category == ContactCategory.CONSULTING_REQUEST
    assert classification_result.confidence_score >= 0.9