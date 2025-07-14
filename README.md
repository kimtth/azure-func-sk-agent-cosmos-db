# 🤖 Agent with Azure Function and Cosmos DB Conversation History

This repo has an Azure Function app that uses managed identity to save conversation history in Cosmos DB and works with Semantic Kernel.

## 🌐 Deploy Azure Function App to Azure

1. ✅ **Allow Remote Build**
    - Navigate to your Function App → Configuration → Check `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
    - Command:
        ```bash
        az functionapp config appsettings set -g <resource-group> -n <app-name> --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true
        ```

2. 🚀 **Deploy with Remote Build**
    - ⚠️ **Note:** Basic/Free Tier App Service Plan does not support remote builds, especially for Python/Azure Functions.
    - Command:
        ```bash
        func azure functionapp publish <app-name> --build remote
        ```

## 🗂️ CosmosDB with Managed Identity

- **Assign Cosmos DB Data Plane Role to resources**: Data Plane Roles (❌ Not Visible in Azure Portal IAM). These roles are part of Cosmos DB’s native RBAC system, which is separate from Azure RBAC. Microsoft has not yet integrated these into the IAM UI, so they must be managed via the console:
- You need to have 2 principal IDs: one for your local development via signed-user, and another for your function app principal ID.

1. 🧹 **Optional:** Clear Azure Account
    ```bash
    az account clear
    ```
2. 🔍 **Get Your Principal IDs**
- **Current Logged-in User Principal ID:**
    ```bash
    az login --tenant TENANT_ID
    az ad signed-in-user show
    ```
- **Azure Function App's Principal ID:**
    ```bash
    az functionapp identity show \
    --name <your-function-app-name> \
    --resource-group <your-resource-group> \
    --query principalId \
    --output tsv
    ```
    OR navigate to `Azure portal > Function App > Identity > System Assigned > Status: On > <Your Principal ID>`
3. 📜 **Optional: Cosmos DB Data Plane Role Definition ID**
    - The command will return `00000000-0000-0000-0000-000000000002`.
    ```bash
    az cosmosdb sql role definition list \
    --account-name <your-cosmosdb-account-name> \
    --resource-group <your-resource-group>
    ```
4. 🛠️ **Assign Cosmos DB Data Plane Role to Principal IDs**
   ```bash
   az cosmosdb sql role assignment create \
   --account-name <your-cosmosdb-account-name> \
   --resource-group <your-resource-group> \
   --scope "/" \
   --principal-id <your-managed-identity-object-id> \
   --role-definition-id "00000000-0000-0000-0000-000000000002"
   ```
5. ✅ **Verify Role Assignment**
   ```bash
   az cosmosdb sql role assignment list \
   --account-name <your-cosmosdb-account-name> \
   --resource-group <your-resource-group>
   ```
6. 🚀 **Deploy Your Function App**
   ```bash
   func azure functionapp publish <your-function-app-name> --python
   ```

### 💡Tips

- 🛑 **To resolve FUNCTIONS_WORKER_RUNTIME invalid error**: <i>Error: The following app setting (Site.SiteConfig.AppSettings.FUNCTIONS_WORKER_RUNTIME) for Flex Consumption sites is invalid. Please remove or rename it before retrying.</i>: Do not add `"FUNCTIONS_WORKER_RUNTIME" : "python"` in `local.settings.json`.
- 🔑 **AzureWebJobsStorage:** Assign the “Storage Blob Data Contributor” role to Azure Functions.
- 📦 **Dependency Management:** Azure Functions does not natively support Poetry for dependency management. It expects a `requirements.txt` file to install Python dependencies during deployment. The command for converting `poetry.toml` to `requirements.txt` 
  ```bash
  poetry export -f requirements.txt --without-hashes -o requirements.txt
  ```

### 📚Learn more

1. [Quickstart: Create a function in Azure with Python using Visual Studio Code](https://learn.microsoft.com/en-us/azure/azure-functions/create-first-function-vs-code-python)
2. [Connect Azure Functions to Azure Cosmos DB using Visual Studio Code](https://learn.microsoft.com/en-us/azure/azure-functions/functions-add-output-binding-cosmos-db-vs-code?pivots=programming-language-python)
3. [Chat History with Azure Cosmos DB and Semantic Kernel](https://stochasticcoder.com/2025/01/27/chat-history-with-azure-cosmos-db-and-semantic-kernel/) [git](https://github.com/jonathanscholtes/Azure-AI-RAG-CSharp-Semantic-Kernel-Functions)