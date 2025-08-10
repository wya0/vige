<template>
  <div class="login">
    <img class="bg" src="../assets/images/login-bg.png"
         alt="">
    <div class="content">
      <img class="logo" src="../assets/images/td-logo.png" alt="">
      <div class="info-content" @keydown.enter="onLogin" key="login-form">
        <div class="form">
          <div class="input-title">手机号</div>
          <div class="input-wrapper">
            <input class="input" type="text" v-model="form.mobile" placeholder="请输入手机号">
          </div>
          <div class="input-title">验证码</div>
          <div class="input-wrapper">
            <input class="input" type="text" v-model="form.code" placeholder="请输入验证码">
            <div class="code" @click="sendCode" :disabled="isCounting">
              {{ isCounting ? countDown : '获取验证码' }}
            </div>
          </div>
          <Button
              style="margin-top: 50px; border: none; background-color: #245BFF; height:44px; border-radius: 22px; color: white; font-size: 14px; font-weight: bold"
              @click="onLogin" :type="buttonType"
              long>{{ buttonTitle }}
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import {isValidMobile} from '@/libs/util'
  import config from '@/config'

  export default {
    name: 'login',

    data () {
      return {
        isLogin: true,
        isCounting: false,
        countDown: 60,
        timer: null,
        form: {
          account: null,
          mobile: null,
          code: null
        },

      }
    },

    computed: {
      buttonType () {
        return this.isLogin ? 'primary' : 'success'
      },

      buttonTitle () {
        return this.isLogin ? '登陆' : '注册'
      },
    },

    methods: {
      async onLogin () {
        if (!this.form.mobile || this.form.mobile.trim().length === 0) {
          this.$Message.error('请输入手机号')
          return
        }
        if (!this.form.code || this.form.code.trim() === '') {
          this.$Message.error('请输入验证码')
          return
        }

        let bindId = this.$store.getters.bindId || localStorage.getItem('bind_id')
        let data = this.form
        if (bindId) {
          data = Object.assign({}, this.form, { bind_id: bindId })
        }
        data = Object.assign({}, data, {  source: 'edu'})
        this.$store.dispatch('login', {
          vue: this,
          loginData: data
        })
        this.timer && clearInterval(this.timer)

      },

      async sendCode () {
        if (this.isCounting) {
          return
        }
        if (!this.form.mobile) {
          this.$Message.error('请输入手机号')
          return
        }
        if (!isValidMobile(this.form.mobile)) {
          this.$Message.error('手机号码不合法')
          return
        }
        let resp = await this.$http.post('/web/send_code', {
          mobile: this.form.mobile,
          verify_type: 'login'
        })
        if (resp.success) {
          this.$Message.success('验证码已发送')
          this.countDown = 60
          this.isCounting = true
          this.timer = setInterval(() => {
            if (this.countDown <= 0) {
              this.timer && clearInterval(this.timer)
              this.isCounting = false
              return
            }
            this.countDown--
          }, 1000)
        }
      },

    },

    async mounted () {

    },

    destroyed () {
      this.timer && clearInterval(this.timer)
    }
  }
</script>

<style scoped lang="less">
  /deep/ .ivu-input-prefix {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
  }

  /deep/ .ivu-input-with-prefix {
    padding-left: 40px;
  }

  /deep/ .ivu-upload-drag {
    border: none;
    background-color: transparent;
  }

  /deep/ .ivu-input-large {
    height: 44px;
    background-color: transparent;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    color: #333333;
  }

  .login {
    background-color: #f1f1f1;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;

    .title {
      width: 100%;
      font-size: 18px;
      font-weight: bold;
      text-align: center;
      margin-bottom: 30px;
    }

    .bg {
      position: absolute;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .content {
      background-color: white;
      width: 500px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      padding: 50px 60px;
      border-radius: 30px;
      overflow: hidden;
      position: relative;
      
      .logo {
        height: 70px;
        width: auto;
        margin-bottom: 30px;
      }

      .input-wrapper {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        border-bottom: 1px solid #eaeaea;
      }

      .input {
        border: none;
        height: 44px;
        font-size: 14px;
        outline: none;
        color: #333333;
      }

      .code {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 6px 18px;
        background-color: #245BFF;
        height: 32px;
        border-radius: 16px;
        color: white;
      }
    }

    .info {
      margin-top: 20px;
      width: 100%;
      text-align: center;
      font-size: 13px;
      color: white;
      cursor: pointer;
      //font-weight: bold;
    }

    .notice {
      font-size: 12px;
      color: #8B8989;
      margin-top: 10px;
      line-height: 16px;
    }
  }

  .login-title {
    font-size: 32px;
    font-weight: bold;
    color: white;
    margin-bottom: 35px;
  }

  .info-content {
    width: 100%;

    .input-title {
      font-size: 16px;
      color: #333333;
      font-weight: bold;
      padding: 20px 0 10px;

      &:first-child {
        margin-top: 0;
      }
    }

    .form {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      justify-content: flex-start;
      width: 100%;

      .title {
        font-size: 14px;
        color: #333333;
        font-weight: bold;
        padding: 10px 0;
      }

      .desc {
        margin-top: 12px;
        font-size: 12px;
        color: rgba(0, 0, 0, 0.6);
      }

      img {
        width: 17px;
        height: 17px;
        margin-left: 5px;
      }
    }

  }

  @media screen and (max-width: 600px) {
    .login {
      .left {
        width: 100%;
        background-color: rgba(0, 0, 0, 0.72);
      }

      .full {
        .place {
          display: none;

        }

        .gpt-intro {
          display: none;
        }
      }

      .info {
        margin-top: 35px;
      }

      .notice {
        color: white;
      }
    }

    .info-content {
      width: 100%;
      padding: 30px;

      .form {
        width: 100%;
      }
    }
  }
</style>