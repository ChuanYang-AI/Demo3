# 酒店AI微调系统架构与流程图

## 📋 文档概述

本文档包含酒店服务AI智能助手微调项目的完整系统架构图和业务流程图，基于Google Cloud Platform的Vertex AI Gemini微调解决方案。

## 🏗️ 系统整体架构图

```mermaid
graph TB
    %% 数据层
    subgraph "数据层 Data Layer"
        A[原始数据集<br/>hotel_train_data.jsonl<br/>1,080条记录]
        B[高质量数据集<br/>923条筛选后数据<br/>85.5%保留率]
        C[验证数据集<br/>231条验证数据<br/>20%分割]
    end
    
    %% 数据处理层
    subgraph "数据处理层 Data Processing Layer"
        D[规则预筛选器<br/>Rule-based Filter]
        E[AI质量评估器<br/>Gemini 2.5 Flash]
        F[数据格式转换器<br/>Google AI Format]
    end
    
    %% 模型训练层
    subgraph "模型训练层 Model Training Layer"
        G[Vertex AI Platform]
        H[Gemini 2.0 Flash<br/>基础模型]
        I[超参数优化器<br/>15轮系统性调优]
        J[微调作业管理器<br/>SFT Training Job]
    end
    
    %% 模型部署层
    subgraph "模型部署层 Model Deployment Layer"
        K[微调后模型<br/>Hotel-Assistant-Tuned]
        L[模型版本管理<br/>Model Registry]
        M[API服务<br/>Prediction Endpoint]
    end
    
    %% 应用服务层
    subgraph "应用服务层 Application Layer"
        N[客服系统集成<br/>Customer Service]
        O[多渠道接入<br/>Multi-channel Access]
        P[实时监控<br/>Performance Monitoring]
    end
    
    %% 存储服务
    subgraph "存储服务 Storage Services"
        Q[Cloud Storage<br/>数据存储]
        R[BigQuery<br/>分析数据库]
        S[Firestore<br/>配置管理]
    end
    
    %% 数据流连接
    A --> D
    D --> E
    E --> B
    B --> F
    F --> C
    
    %% 训练流程
    B --> G
    C --> G
    H --> G
    I --> G
    G --> J
    J --> K
    
    %% 部署流程
    K --> L
    L --> M
    M --> N
    N --> O
    
    %% 监控反馈
    O --> P
    P --> R
    
    %% 存储连接
    B --> Q
    C --> Q
    K --> Q
    P --> R
    I --> S
    
    %% 样式定义
    classDef dataClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef processClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef modelClass fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef deployClass fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef appClass fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef storageClass fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    
    class A,B,C dataClass
    class D,E,F processClass
    class G,H,I,J modelClass
    class K,L,M deployClass
    class N,O,P appClass
    class Q,R,S storageClass
```

## 📊 数据质量控制流程图

```mermaid
flowchart TD
    %% 数据输入
    Start([开始]) --> Input[原始数据输入<br/>hotel_train_data.jsonl<br/>1,080条记录]
    
    %% 第一阶段筛选
    Input --> Stage1{第一阶段<br/>规则预筛选}
    Stage1 --> Rule1[酒店关键词检查<br/>30+专业术语验证]
    Rule1 --> Rule2[格式完整性验证<br/>问答结构检查]
    Rule2 --> Rule3[长度合理性检查<br/>问题8-120字符<br/>回答30-1200字符]
    Rule3 --> Rule4[语言规范性验证<br/>表达专业性检查]
    
    %% 规则筛选结果
    Rule4 --> RuleResult{规则筛选结果<br/>通过率99.9%}
    RuleResult -->|通过| Stage2{第二阶段<br/>AI质量评估}
    RuleResult -->|不通过| Reject1[规则拒绝<br/>1条数据]
    
    %% AI质量评估
    Stage2 --> AIBatch[批量处理<br/>12条目/批次<br/>6线程并发]
    AIBatch --> AIModel[Gemini 2.5 Flash<br/>质量评估模型]
    AIModel --> AIScore[多维度评分<br/>1-10分评价<br/>问题清晰度<br/>回答专业性<br/>逻辑一致性]
    
    %% AI评估结果
    AIScore --> ScoreCheck{评分检查<br/>≥7分为高质量}
    ScoreCheck -->|≥7分| Accept[接受数据<br/>923条高质量数据<br/>85.5%保留率]
    ScoreCheck -->|<7分| Reject2[质量拒绝<br/>157条低质量数据<br/>14.5%淘汰率]
    
    %% 数据分割
    Accept --> Split[数据分割<br/>80/20比例]
    Split --> TrainSet[训练集<br/>923条数据]
    Split --> ValidSet[验证集<br/>231条数据]
    
    %% 格式转换
    TrainSet --> Format1[Google AI格式转换<br/>systemInstruction + contents]
    ValidSet --> Format2[Google AI格式转换<br/>systemInstruction + contents]
    
    %% 质量报告
    Accept --> Report[生成质量报告<br/>详细分析统计]
    Reject1 --> Report
    Reject2 --> Report
    
    %% 输出
    Format1 --> Output1[高质量训练数据<br/>hotel_high_quality_train.jsonl]
    Format2 --> Output2[高质量验证数据<br/>hotel_high_quality_validation.jsonl]
    Report --> Output3[数据质量报告<br/>hotel_quality_report.json]
    
    Output1 --> End([结束])
    Output2 --> End
    Output3 --> End
    
    %% 样式定义
    classDef startEnd fill:#4caf50,stroke:#2e7d32,stroke-width:3px,color:#fff
    classDef process fill:#2196f3,stroke:#1565c0,stroke-width:2px,color:#fff
    classDef decision fill:#ff9800,stroke:#ef6c00,stroke-width:2px,color:#fff
    classDef reject fill:#f44336,stroke:#c62828,stroke-width:2px,color:#fff
    classDef accept fill:#4caf50,stroke:#2e7d32,stroke-width:2px,color:#fff
    classDef output fill:#9c27b0,stroke:#6a1b9a,stroke-width:2px,color:#fff
    
    class Start,End startEnd
    class Input,Rule1,Rule2,Rule3,Rule4,AIBatch,AIModel,AIScore,Split,Format1,Format2,Report process
    class Stage1,Stage2,RuleResult,ScoreCheck decision
    class Reject1,Reject2 reject
    class Accept,TrainSet,ValidSet accept
    class Output1,Output2,Output3 output
```

## 🔄 模型微调训练流程图

```mermaid
flowchart TD
    %% 训练准备
    Start([开始微调训练]) --> DataPrep[数据准备<br/>923条训练数据<br/>231条验证数据]
    DataPrep --> ModelSelect[模型选择<br/>Gemini 2.0 Flash]
    
    %% 超参数配置
    ModelSelect --> HyperConfig[超参数配置<br/>基于15轮优化经验]
    HyperConfig --> Config1[学习率乘数: 0.5<br/>最优稳定配置]
    Config1 --> Config2[训练轮数: 2 Epochs<br/>防过拟合最佳平衡]
    Config2 --> Config3[批次大小: 4<br/>内存效率优化]
    Config3 --> Config4[验证分割: 20%<br/>充分验证覆盖]
    
    %% 训练执行
    Config4 --> TrainJob[创建SFT训练作业<br/>Vertex AI Platform]
    TrainJob --> TrainStart[开始训练<br/>约70分钟预计时长]
    
    %% 训练监控
    TrainStart --> Monitor[实时监控<br/>训练指标追踪]
    Monitor --> Metrics[关键指标<br/>训练损失<br/>验证准确率<br/>收敛状态]
    
    %% 收敛检查
    Metrics --> Convergence{收敛检查<br/>60-80步平台期}
    Convergence -->|继续训练| Monitor
    Convergence -->|收敛完成| TrainComplete[训练完成<br/>验证准确率80.3%]
    
    %% 模型验证
    TrainComplete --> Validation[模型验证<br/>验证集性能评估]
    Validation --> Performance[性能指标<br/>训练准确率: 80.5%<br/>验证准确率: 80.3%<br/>训练损失: <0.6<br/>验证损失: <0.6]
    
    %% 过拟合检查
    Performance --> OverfitCheck{过拟合检查<br/>训练/验证指标一致性}
    OverfitCheck -->|存在过拟合| Retrain[重新训练<br/>调整超参数]
    OverfitCheck -->|无过拟合| ModelReady[模型就绪<br/>Hotel-Assistant-Tuned]
    
    %% 模型部署
    ModelReady --> Deploy[模型部署<br/>创建预测端点]
    Deploy --> Endpoint[API端点<br/>生产环境就绪]
    
    %% 性能测试
    Endpoint --> Testing[性能测试<br/>响应时间<br/>并发能力<br/>准确率验证]
    Testing --> TestResult{测试结果评估}
    TestResult -->|不达标| Optimize[性能优化<br/>调整部署配置]
    TestResult -->|达标| Production[生产上线<br/>正式服务]
    
    %% 监控反馈
    Production --> Monitor2[生产监控<br/>实时性能跟踪]
    Monitor2 --> Feedback[用户反馈<br/>服务质量评估]
    Feedback --> Improve[持续改进<br/>模型迭代优化]
    
    %% 重新训练循环
    Retrain --> Config1
    Optimize --> Deploy
    Improve --> DataPrep
    
    Production --> End([微调完成])
    
    %% 样式定义
    classDef startEnd fill:#4caf50,stroke:#2e7d32,stroke-width:3px,color:#fff
    classDef process fill:#2196f3,stroke:#1565c0,stroke-width:2px,color:#fff
    classDef config fill:#9c27b0,stroke:#6a1b9a,stroke-width:2px,color:#fff
    classDef decision fill:#ff9800,stroke:#ef6c00,stroke-width:2px,color:#fff
    classDef important fill:#f44336,stroke:#c62828,stroke-width:2px,color:#fff
    classDef success fill:#4caf50,stroke:#2e7d32,stroke-width:2px,color:#fff
    
    class Start,End startEnd
    class DataPrep,ModelSelect,TrainJob,TrainStart,Monitor,Validation,Deploy,Endpoint,Testing,Monitor2,Feedback process
    class HyperConfig,Config1,Config2,Config3,Config4 config
    class Convergence,OverfitCheck,TestResult decision
    class Retrain,Optimize,Improve important
    class TrainComplete,Performance,ModelReady,Production success
```

## 🔧 技术组件架构图

```mermaid
graph LR
    %% 数据处理组件
    subgraph "数据处理组件 Data Processing"
        A[数据质量筛选器<br/>HotelDataQualityFilter]
        B[规则引擎<br/>RuleEngine]
        C[AI评估器<br/>AIQualityEvaluator]
        D[格式转换器<br/>DataFormatter]
    end
    
    %% 模型训练组件
    subgraph "模型训练组件 Model Training"
        E[Vertex AI管理器<br/>VertexAIManager]
        F[超参数优化器<br/>HyperparameterOptimizer]
        G[训练作业管理器<br/>TrainingJobManager]
        H[性能监控器<br/>PerformanceMonitor]
    end
    
    %% 部署服务组件
    subgraph "部署服务组件 Deployment Services"
        I[模型部署器<br/>ModelDeployer]
        J[API网关<br/>APIGateway]
        K[负载均衡器<br/>LoadBalancer]
        L[服务监控器<br/>ServiceMonitor]
    end
    
    %% 存储组件
    subgraph "存储组件 Storage Components"
        M[Cloud Storage<br/>数据存储]
        N[BigQuery<br/>分析数据库]
        O[Firestore<br/>配置存储]
        P[Model Registry<br/>模型仓库]
    end
    
    %% 工具组件
    subgraph "工具组件 Utility Components"
        Q[日志管理器<br/>LoggerManager]
        R[配置管理器<br/>ConfigManager]
        S[错误处理器<br/>ErrorHandler]
        T[性能分析器<br/>PerformanceAnalyzer]
    end
    
    %% 组件间连接
    A --> B
    A --> C
    A --> D
    B --> M
    C --> M
    D --> M
    
    E --> F
    E --> G
    E --> H
    F --> O
    G --> P
    H --> N
    
    I --> J
    I --> K
    I --> L
    J --> P
    K --> L
    L --> N
    
    %% 工具组件连接
    Q --> N
    R --> O
    S --> Q
    T --> N
    
    %% 跨组件连接
    D --> E
    G --> I
    H --> L
    
    %% 样式定义
    classDef dataComp fill:#e3f2fd,stroke:#0277bd,stroke-width:2px
    classDef modelComp fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef deployComp fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef storageComp fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef utilComp fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    
    class A,B,C,D dataComp
    class E,F,G,H modelComp
    class I,J,K,L deployComp
    class M,N,O,P storageComp
    class Q,R,S,T utilComp
```

## 📱 业务应用流程图

```mermaid
sequenceDiagram
    participant Customer as 客户
    participant Frontend as 前端应用
    participant Gateway as API网关
    participant Model as 微调模型
    participant Monitor as 监控系统
    participant Database as 数据库
    
    %% 客户请求
    Customer->>Frontend: 发送服务咨询
    note over Customer,Frontend: "客房WiFi连接不上，如何处理？"
    
    %% 请求处理
    Frontend->>Gateway: 转发请求
    Gateway->>Gateway: 身份验证
    Gateway->>Gateway: 请求预处理
    
    %% 模型推理
    Gateway->>Model: 调用微调模型
    note over Model: 基于酒店服务专业训练
    Model->>Model: 语义理解
    Model->>Model: 专业知识推理
    Model->>Model: 结构化回答生成
    
    %% 返回结果
    Model->>Gateway: 返回专业回答
    note over Model,Gateway: 包含完整处理流程和服务标准
    Gateway->>Frontend: 返回格式化响应
    Frontend->>Customer: 展示专业回答
    
    %% 监控记录
    par 并行监控
        Gateway->>Monitor: 记录请求指标
        Model->>Monitor: 记录模型性能
        Monitor->>Database: 存储监控数据
    end
    
    %% 质量反馈
    Customer->>Frontend: 服务质量评价
    Frontend->>Database: 存储反馈数据
    Database->>Monitor: 触发质量分析
    
    %% 持续优化
    alt 需要优化
        Monitor->>Model: 触发模型更新
        note over Monitor,Model: 基于反馈数据持续改进
    else 性能良好
        Monitor->>Database: 记录成功案例
    end
```

```

## 📋 图表说明

### 系统整体架构图
- **数据层**：展示从原始数据到高质量数据的处理过程
- **数据处理层**：包含规则筛选和AI评估的双重质量控制
- **模型训练层**：基于Vertex AI的完整训练流程
- **模型部署层**：从模型到API服务的部署架构
- **应用服务层**：面向客户的服务接入和监控
- **存储服务**：支撑整个系统的存储架构

### 数据质量控制流程图
- **两阶段筛选**：规则预筛选（99.9%通过率）+ AI质量评估（85.5%保留率）
- **多维度评估**：问题清晰度、回答专业性、逻辑一致性
- **质量保证**：从1,080条原始数据筛选出923条高质量训练数据

### 模型微调训练流程图
- **系统性优化**：基于15轮实验的最优配置
- **防过拟合策略**：调整Epochs ，降低学习率等
- **实时监控**：训练过程的关键指标追踪
- **持续改进**：生产环境反馈的闭环优化

### 技术组件架构图
- **模块化设计**：5大组件分类，职责清晰
- **松耦合架构**：组件间通过标准接口交互
- **可扩展性**：支持水平扩展和功能扩展
- **高可用性**：关键组件的冗余和容错设计

### 业务应用流程图
- **端到端流程**：从客户请求到专业回答的完整链路
- **并行处理**：监控和业务逻辑的并行执行
- **质量反馈**：用户评价驱动的持续优化
- **实时监控**：全链路的性能和质量监控


---
*文档基于真实微调项目架构*  
*图表使用Mermaid语法，支持在线渲染*  
*最后更新：近期* 