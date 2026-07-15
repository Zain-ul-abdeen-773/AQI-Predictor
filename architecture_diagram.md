# System Architecture: AQI Predictor

This diagram illustrates the end-to-end automated architecture of the AQI Predictor, showing how data flows, how the model is trained, and how the web dashboard is served.

```mermaid
flowchart TD
    %% Define Styles
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:white;
    classDef github fill:#181717,stroke:#fff,stroke-width:2px,color:white;
    classDef ext fill:#4285F4,stroke:#fff,stroke-width:2px,color:white;
    classDef store fill:#13A89E,stroke:#fff,stroke-width:2px,color:white;
    classDef client fill:#34A853,stroke:#fff,stroke-width:2px,color:white;

    %% External Sources
    User((User / Browser)):::client
    AQICN([AQICN API]):::ext
    OpenWeather([OpenWeather API]):::ext
    GitHub([GitHub Repository]):::github
    HopsworksFS[(Hopsworks Feature Store)]:::store
    HopsworksMR[(Hopsworks Model Registry)]:::store

    subgraph AWS Cloud Architecture
        direction TB

        subgraph CI/CD Pipeline
            direction LR
            Pipeline(AWS CodePipeline):::aws
            Build(AWS CodeBuild):::aws
            ECR[(Amazon ECR)]:::aws
        end

        subgraph Automated Pipelines
            CronHour([EventBridge: Hourly]):::aws
            CronDay([EventBridge: Daily]):::aws
            
            FeatPipe[Lambda: Feature Pipeline]:::aws
            TrainPipe[ECS Fargate: Training Pipeline]:::aws
            
            CronHour -. triggers .-> FeatPipe
            CronDay -. triggers .-> TrainPipe
        end

        subgraph Serving Layer
            LambdaURL([Lambda Function URL]):::aws
            APILambda[Lambda: API / Dashboard]:::aws
        end
    end

    %% CI/CD Flow
    GitHub -- "Push to main" --> Pipeline
    Pipeline -- "Triggers Build" --> Build
    Build -- "Builds & Pushes Image" --> ECR
    ECR -. "Provides latest image" .-> FeatPipe
    ECR -. "Provides latest image" .-> TrainPipe
    ECR -. "Provides latest image" .-> APILambda

    %% Feature Pipeline Flow
    FeatPipe -- "Fetches Data" --> AQICN
    FeatPipe -- "Fetches Data" --> OpenWeather
    FeatPipe -- "Writes Features" --> HopsworksFS

    %% Training Pipeline Flow
    TrainPipe -- "Reads Features" --> HopsworksFS
    TrainPipe -- "Trains & Saves Model" --> HopsworksMR

    %% Serving Flow
    User -- "HTTP GET /" --> LambdaURL
    LambdaURL -- "Invokes via Mangum" --> APILambda
    APILambda -- "Reads Features" --> HopsworksFS
    APILambda -- "Loads Model" --> HopsworksMR
```

### Architecture Breakdown

1. **CI/CD Pipeline (Automated Deployments)**
   - When you push code to GitHub, **AWS CodePipeline** automatically triggers.
   - **AWS CodeBuild** builds the Docker image and pushes it to **Amazon ECR**.
   - The Lambda functions and ECS tasks are configured to run this newly built image.

2. **Feature Pipeline (Hourly)**
   - Triggered every hour by **AWS EventBridge**.
   - Runs as an **AWS Lambda function**.
   - Fetches live air quality data (AQICN) and weather data (OpenWeather) and stores them in the **Hopsworks Feature Store**.

3. **Training Pipeline (Daily)**
   - Triggered every day by **AWS EventBridge**.
   - Runs as an **AWS ECS Fargate task** (since model training is compute-intensive and can take longer than Lambda's 15-minute limit).
   - Pulls historical features from Hopsworks, trains the Machine Learning model, and uploads the new version to the **Hopsworks Model Registry**.

4. **Serving Layer (Web Dashboard)**
   - The user visits the **AWS Lambda Function URL**.
   - The request hits the **API Lambda Function**, which runs your `FastAPI` app (adapted via `Mangum`).
   - The API dynamically pulls the latest model and the latest live features from Hopsworks to serve the real-time predictions to the dashboard.
