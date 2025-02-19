<h1>Activity Diagrams for User Authentication and Transaction Handling</h1>

<h2>Purpose</h2>

These activity diagrams illustrate the workflows for user authentication and transaction handling within RevoBank's web-based application. They serve as blueprints to guide the development team in implementing these functionalities efficiently. This workflow is inspired by paypal. 

The diagrams follow UML standards, including action states, decision nodes, and transitions. Decision nodes are represented for error handling and verification steps. These diagrams provide a structured visualization of authentication and transaction workflows, ensuring secure and efficient banking processes within RevoBank.

To access the diagram: 

``
## Installation Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/revou-fsse-oct24/milestone-3-rifqisaleh.git
   ```
2. Navigate to the project directory:
   ```bash
   cd Revoubank-Project
   ```
3. Open UML Diagram inside within the directory



<br>

<h3> 1. User Authentication Activity Diagram </h3>

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

* Email Notification<br> <br>
<br> <br>



<h3> 2. Transaction Handling Activity Diagram </h3>

Description:
This diagram depicts the process of handling transactions, including deposits, withdrawals, and transfers.

Key Processes:

* The user accesses the account overview page and initiates a transaction.

* The system verifies account balance.

* If the balance is insufficient, the transaction fails, and an email with transaction details is sent.

* If sufficient funds exist, the transaction is processed, generating an invoice.

* Bank/credit card verification is performed.

* If verification fails, the transaction is marked as failed.

* If verification is successful, a paid invoice is printed, the transaction history is generated, and transaction details are sent to the user's email.

Actors:

* User

* Transaction Service

* Account Verification System

* Bank/Credit Card Verification Service

* Email Notification System