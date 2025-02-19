Activity Diagrams for User Authentication and Transaction Handling

Purpose

These activity diagrams illustrate the workflows for user authentication and transaction handling within RevoBank's web-based application. They serve as blueprints to guide the development team in implementing these functionalities efficiently.

UML Compliance

The diagrams follow UML standards, including action states, decision nodes, and transitions.

Decision nodes are represented for error handling and verification steps.

These diagrams provide a structured visualization of authentication and transaction workflows, ensuring secure and efficient banking processes within RevoBank.



1. User Authentication Activity Diagram

Description:
This diagram outlines the login process, including credential verification, error handling, email notifications, and token generation.

Key Processes:

* The user enters login credentials.

* The system verifies the credentials.

* If the credentials are incorrect, an email notification is sent, and the login attempt is recorded.

* If multiple failed attempts occur, the account is locked.

* Upon successful verification, a token is generated, granting the user access.

Actors:

* Registered User

* Authentication Service

* Email Notification



2. Transaction Handling Activity Diagram

Description:
This diagram depicts the process of handling transactions, including deposits, withdrawals, and transfers.

Key Processes:

* The user initiates a transaction.

* The system verifies account balance.

* If the balance is insufficient, the user is prompted to retry.

* If sufficient funds exist, the transaction is processed.

* A transaction history is generated and stored.

Actors:

* User

* Transaction Service

* Account Verification System
