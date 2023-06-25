# jsocom-contact-services
code &amp; terraform to power contact-me forms on johnsosoka.com


## Services Overview

### contact-listener

This service receives contact messages via HTTP POST and sends them to `contact-message-queue` SQS queue.

## contact-filter

This service will read messages off of the `contact-message-queue` queue. 

* If the IP/User Agent is blocked it will persist the `all-contact-messages` DynamooDB table with the flag "blocked=true"
* If the IP/User Agent is not blocked it will forward messages to a `contact-notify-queue` SQS queue.

## contact-notifier

Reads messages from the `contact-notify` SQS queue and sends them to the configured email address.

## contact-administration

Service provides several methods for contact administration

* block contact
* unblock contact
* list blocked contacts
* view all blocked messages
