# Table for savings all contact messages
resource "aws_dynamodb_table" "all_contact_messages" {
  name = "all-contact-messages"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "id"
  range_key = "timestamp"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  attribute {
    name = "sender_name"
    type = "S"
  }

  attribute {
    name = "sender_email"
    type = "S"
  }

  attribute {
    name = "message_body"
    type = "S"
  }

  attribute {
    name = "is_blocked"
    type = "N"
  }

  global_secondary_index {
    name               = "sender_name-index"
    hash_key           = "sender_name"
    projection_type    = "ALL"
    write_capacity     = 1
    read_capacity      = 1
  }

  global_secondary_index {
    name               = "sender_email-index"
    hash_key           = "sender_email"
    projection_type    = "ALL"
    write_capacity     = 1
    read_capacity      = 1
  }

  global_secondary_index {
    name               = "is_blocked-index"
    hash_key           = "is_blocked"
    projection_type    = "ALL"
    write_capacity     = 1
    read_capacity      = 1
  }

  global_secondary_index {
    name               = "message-body-index"
    hash_key           = "message_body"
    projection_type    = "ALL"
    write_capacity     = 1
    read_capacity      = 1
  }
}

# Table for tracking blocked contacts
resource "aws_dynamodb_table" "blocked_contacts" {
  name           = "blocked_contacts"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "ip_address"
    type = "S"
  }

  attribute {
    name = "user_agent"
    type = "S"
  }

  attribute {
    name = "is_blocked"
    type = "N"
  }

  global_secondary_index {
    name               = "ip_address-index"
    hash_key           = "ip_address"
    projection_type    = "ALL"
    write_capacity     = 1
    read_capacity      = 1
  }

  global_secondary_index {
    name               = "user_agent-index"
    hash_key           = "user_agent"
    projection_type    = "ALL"
    write_capacity     = 1
    read_capacity      = 1
  }

  global_secondary_index {
    name               = "is_blocked-index"
    hash_key           = "is_blocked"
    projection_type    = "ALL"
    write_capacity     = 1
    read_capacity      = 1
  }

  global_secondary_index {
    name               = "ip_address-user_agent-index"
    hash_key           = "ip_address"
    range_key          = "user_agent"
    projection_type    = "ALL"
    write_capacity     = 1
    read_capacity      = 1
  }
}
