<template>
  <div class="container">
    <div class="home">
      <div class="header">
        <h1>AI提示词生成助手</h1>
        <p>帮助您快速创建专业、结构化、易于AI理解的提示词</p>
      </div>

      <!-- 上部分：结果展示区（左右分栏） -->
      <div class="result-section">
        <!-- 左侧：提示词内容 -->
        <div class="prompt-column">
          <div class="column-header">
            <h2>生成的提示词</h2>
            <div v-if="generatedPrompt" class="actions">
              <Button type="text" @click="copyToClipboard(generatedPrompt)">
                <Icon type="md-copy" />复制
              </Button>
            </div>
          </div>
          
          <div class="column-content">
            <!-- 有内容时显示 -->
            <Card v-if="generatedPrompt">
              <div class="markdown-content" v-html="formattedGeneratedPrompt"></div>
            </Card>
            
            <!-- 无内容时显示占位提示 -->
            <div v-else class="placeholder">
              <Icon type="ios-document-outline" size="60" />
              <p>您生成的提示词将显示在这里</p>
            </div>
          </div>
        </div>
        
        <!-- 右侧：预览效果 -->
        <div class="preview-column">
          <div class="column-header">
            <h2>提示词效果预览</h2>
          </div>
          
          <div class="column-content">
            <!-- 有内容时显示 -->
            <Card v-if="promptExample">
              <div class="markdown-content" v-html="formattedPromptExample"></div>
            </Card>
            
            <!-- 无内容时显示占位提示 -->
            <div v-else class="placeholder">
              <Icon type="ios-eye-outline" size="60" />
              <p>生成提示词后，效果预览将显示在这里</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 下部分：用户输入区 -->
      <div class="input-section">
        <Card>
          <div class="input-controls">
            <div class="model-select">
              <span>选择AI模型：</span>
              <Select v-model="selectedModel" style="width: 200px">
                <Option v-for="model in aiModels" :key="model.id" :value="model.id">{{ model.name }}</Option>
              </Select>
            </div>
            
            <Button 
              type="primary" 
              :loading="isLoading" 
              @click="generatePrompt"
              :disabled="!canSubmit"
              class="generate-btn"
            >
              {{ generatedPrompt ? '重新生成' : '生成提示词' }}
            </Button>
          </div>
          
          <div class="input-area">
            <Input 
              v-model="userInput" 
              type="textarea" 
              :rows="5" 
              placeholder="请描述您的需求，例如：我需要一个可以帮助我分析财务数据并提供投资建议的提示词。描述越详细，生成的提示词越准确。"
              :disabled="isLoading"
            />
          </div>
          
          <!-- 反馈区域 -->
          <div v-if="generatedPrompt" class="feedback-area">
            <div class="feedback-header">
              <h3>不满意？告诉我们如何改进</h3>
            </div>
            
            <div class="feedback-input">
              <Input 
                v-model="feedbackInput" 
                type="textarea" 
                :rows="3" 
                placeholder="例如：我希望提示词更加具体一些，增加关于..."
                :disabled="isLoading"
              />
            </div>
            
            <div class="feedback-button">
              <Button 
                type="default" 
                :loading="isLoading" 
                @click="submitFeedback"
                :disabled="!canSubmitFeedback"
              >
                提交反馈并优化
              </Button>
            </div>
          </div>
        </Card>
      </div>

      <!-- 加载中遮罩 -->
      <div v-if="isLoading" class="loading-mask">
        <Spin size="large" fix>
          <Icon type="ios-loading" size="44" class="spin-icon-load"></Icon>
          <div class="spin-text">正在生成中，请稍候...</div>
        </Spin>
      </div>
      
      <!-- 历史提示词 -->
      <div v-if="promptHistory.length > 0" class="history-container">
        <div class="history-header">
          <h2>历史生成</h2>
          <p>您之前生成的提示词</p>
        </div>
        
        <div class="history-list">
          <Card v-for="(item, index) in promptHistory" :key="index" class="history-item">
            <p slot="title">
              <span>{{ item.title || '无标题提示词' }}</span>
              <span class="history-date">{{ formatDate(item.created_at) }}</span>
            </p>
            <p>{{ truncateText(item.steps && item.steps.length > 0 ? item.steps[0].user_input : '', 100) }}</p>
            <div class="history-actions">
              <Button type="text" size="small" @click="viewPromptDetail(item.id)">查看详情</Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import { formatDatetimeUTC } from '@/libs/filters'
  import moment from 'moment'
  import marked from 'marked'
  import hljs from 'highlight.js'
  import 'highlight.js/styles/atom-one-dark.css' // 代码高亮主题

  export default {
    name: 'Home',

    data () {
      return {
        // 用户输入
        userInput: '',
        selectedModel: null,
        
        // 生成结果
        generatedPrompt: '',
        promptExample: '',
        
        // 反馈优化
        feedbackInput: '',
        
        // 历史记录
        promptHistory: [],
        
        // 状态控制
        isLoading: false,
        
        // AI模型列表
        aiModels: [],
        
        // 当前提示词相关信息
        currentPromptId: null,
        currentStepId: null
      }
    },

    computed: {
      canSubmit() {
        return this.userInput.trim() && this.selectedModel && !this.isLoading
      },
      
      canSubmitFeedback() {
        return this.feedbackInput.trim() && this.currentPromptId && !this.isLoading
      },
      
      formattedPromptExample() {
        if (!this.promptExample) return ''
        return this.renderMarkdown(this.promptExample)
      },
      
      formattedGeneratedPrompt() {
        if (!this.generatedPrompt) return ''
        return this.renderMarkdown(this.generatedPrompt)
      }
    },

    methods: {
      // 渲染Markdown
      renderMarkdown(text) {
        if (!text) return ''
        return marked(text)
      },
      
      // 生成提示词
      async generatePrompt() {
        if (!this.canSubmit) return
        
        try {
          this.isLoading = true
          
          const requestData = {
            user_input: this.userInput,
            ai_model_type: this.selectedModel
          }
          
          if (this.currentStepId) {
            requestData.last_step_id = this.currentStepId
          }
          
          const response = await this.$http.post('/web/generate/prompts', requestData)
          
          this.currentPromptId = response.prompt_id
          this.currentStepId = response.step_id
          this.generatedPrompt = response.generated_prompt
          
          // 生成一个示例结果
          this.generateExample()
          
          // 获取历史提示词
          this.fetchPromptHistory()
        } catch (error) {
          this.$Message.error('生成提示词失败，请重试')
          console.error('Error generating prompt:', error)
        } finally {
          this.isLoading = false
        }
      },
      
      // 提交反馈并优化
      async submitFeedback() {
        if (!this.canSubmitFeedback) return
        
        try {
          this.isLoading = true
          
          const response = await this.$http.post('/web/prompt_steps', {
            prompt_id: this.currentPromptId,
            last_step_id: this.currentStepId,
            user_input: this.feedbackInput
          })
          
          this.currentStepId = response.step_id
          this.generatedPrompt = response.generated_prompt
          this.feedbackInput = ''
          
          // 生成新的示例
          this.generateExample()
          
          this.$Message.success('提示词已优化')
        } catch (error) {
          this.$Message.error('优化提示词失败，请重试')
          console.error('Error submitting feedback:', error)
        } finally {
          this.isLoading = false
        }
      },
      
      // 生成示例结果
      async generateExample() {
        if (!this.currentStepId) return;
        
        try {
          // 调用API生成示例
          const response = await this.$http.post(`/web/prompt_examples/${this.currentStepId}`);
          
          if (response && response.example_result) {
            this.promptExample = response.example_result;
          }
        } catch (error) {
          console.error('获取示例失败:', error);
          // 如果API调用失败，使用默认示例
          this.promptExample = `这是使用您的提示词可能生成的结果示例。\n\n在实际应用中，这里会展示使用您的提示词得到的AI响应，帮助您评估提示词的效果。\n\n根据您的需求，这个示例会尽可能接近真实场景。`;
        }
      },
      
      // 获取历史提示词列表
      async fetchPromptHistory() {
        try {
          const response = await this.$http.get('/web/prompts', {
            params: {
              page: 1,
              size: 5
            }
          })
          
          this.promptHistory = response.items || []
        } catch (error) {
          console.error('Error fetching prompt history:', error)
        }
      },
      
      // 查看提示词详情
      viewPromptDetail(promptId) {
        this.$router.push(`/prompt/${promptId}`)
      },
      
      // 获取AI模型列表
      async fetchAiModels() {
        try {
          this.aiModels = await this.$http.get('/web/ai_models')
          
          // 设置默认选中的AI模型
          if (this.aiModels && this.aiModels.length > 0) {
            this.selectedModel = this.aiModels[0].id
          }
        } catch (error) {
          console.error('Error fetching AI models:', error)
        }
      },
      
      // 复制文本到剪贴板
      copyToClipboard(text) {
        const textarea = document.createElement('textarea')
        textarea.value = text
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
        this.$Message.success('已复制到剪贴板')
      },
      
      // 格式化日期
      formatDate(date) {
        return moment(date).format('YYYY-MM-DD HH:mm')
      },
      
      // 截断文本
      truncateText(text, maxLength) {
        if (!text) return ''
        if (text.length <= maxLength) return text
        return text.substring(0, maxLength) + '...'
      }
    },

    mounted () {
      // 配置Markdown渲染器
      if (marked) {
        const renderer = new marked.Renderer()
        renderer.code = (code, language) => {
          const validLanguage = hljs.getLanguage(language) ? language : 'plaintext'
          return `<pre><code class="hljs ${validLanguage}">${hljs.highlight(validLanguage, code).value}</code></pre>`
        }
        marked.setOptions({
          renderer,
          highlight: (code) => hljs.highlightAuto(code).value,
          breaks: true,
          gfm: true
        })
      }
      
      this.fetchAiModels()
      this.fetchPromptHistory()
    }
  }
</script>

<style lang="less">
  .container {
    width: 90%;
    margin: 0 auto;
    min-height: 100vh;
    background-color: white;
    padding: 30px 0;
  }

  .home {
    width: 100%;
    height: 100%;
    overflow: auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-bottom: 50px;
  }
  
  .header {
    text-align: center;
    margin-bottom: 30px;
    
    h1 {
      font-size: 28px;
      color: #17233d;
      margin-bottom: 10px;
    }
    
    p {
      color: #808695;
      font-size: 16px;
    }
  }
  
  .result-section {
    width: 90%;
    margin-bottom: 40px;
    display: flex;
    justify-content: space-between;
    min-height: 400px;
  }
  
  .prompt-column, .preview-column {
    width: 48%;
    background-color: #f8f8f9;
    padding: 20px;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    
    .column-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
      
      h2 {
        font-size: 18px;
      }
    }
    
    .column-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      
      .placeholder {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 300px;
        text-align: center;
        color: #808695;
        font-size: 14px;
        
        .ivu-icon {
          margin-bottom: 10px;
          color: #c5c8ce;
        }
      }
      
      .ivu-card {
        height: 100%;
        display: flex;
        flex-direction: column;
        
        .ivu-card-body {
          flex: 1;
          overflow-y: auto;
        }
      }
      
      .markdown-content {
        max-height: 500px;
        overflow-y: auto;
        padding: 10px;
        
        pre {
          background-color: #282c34;
          border-radius: 4px;
          padding: 10px;
          margin: 10px 0;
        }
        
        code {
          font-family: 'Courier New', Courier, monospace;
          font-size: 14px;
        }
        
        h1, h2, h3, h4, h5, h6 {
          margin-top: 16px;
          margin-bottom: 8px;
          font-weight: 600;
        }
        
        p {
          margin-bottom: 10px;
          line-height: 1.5;
        }
        
        ul, ol {
          padding-left: 20px;
          margin-bottom: 10px;
        }
        
        blockquote {
          border-left: 4px solid #ddd;
          padding-left: 16px;
          margin-left: 0;
          color: #666;
        }
        
        table {
          border-collapse: collapse;
          width: 100%;
          margin: 10px 0;
          
          th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
          }
          
          th {
            background-color: #f8f8f9;
          }
        }
      }
    }
  }
  
  .input-section {
    width: 90%;
    margin-bottom: 40px;
  }
  
  .input-controls {
    margin-bottom: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .model-select {
    display: flex;
    align-items: center;
    
    span {
      margin-right: 10px;
      white-space: nowrap;
    }
  }
  
  .generate-btn {
    margin-left: 10px;
  }
  
  .input-area {
    margin-bottom: 15px;
  }
  
  .feedback-area {
    margin-top: 20px;
    background-color: #f8f8f9;
    padding: 20px;
    border-radius: 4px;
    
    .feedback-header {
      margin-bottom: 15px;
      
      h3 {
        font-size: 16px;
        margin-bottom: 8px;
      }
    }
    
    .feedback-input {
      margin-bottom: 15px;
    }
    
    .feedback-button {
      display: flex;
      justify-content: flex-end;
    }
  }
  
  .loading-mask {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(255, 255, 255, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    
    .spin-icon-load {
      animation: ani-spin 1s linear infinite;
    }
    
    .spin-text {
      margin-top: 10px;
      font-size: 14px;
      color: #2d8cf0;
    }
  }
  
  @keyframes ani-spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .history-container {
    width: 90%;
    margin-top: 30px;
    
    .history-header {
      margin-bottom: 20px;
      
      h2 {
        font-size: 18px;
        margin-bottom: 8px;
      }
      
      p {
        color: #808695;
        font-size: 14px;
      }
    }
    
    .history-list {
      display: flex;
      flex-direction: column;
      gap: 15px;
    }
    
    .history-item {
      .history-date {
        font-size: 12px;
        color: #808695;
        margin-left: 10px;
      }
      
      .history-actions {
        display: flex;
        justify-content: flex-end;
        margin-top: 10px;
      }
    }
  }
</style>