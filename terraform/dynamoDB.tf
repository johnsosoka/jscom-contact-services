# Table for savings all contact messages
resource "aws_dynamodb_table" "all_contact_messages" {
  name         = "all-contact-messages"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    project = local.project_name
  }
}

# Table for tracking blocked contacts
resource "aws_dynamodb_table" "blocked_contacts" {
  name         = "blocked_contacts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

}
