<template>
  <Layout style="height: 100%" class="main">
    <Layout>
      <Header class="header-con">
        <header-bar :collapsed="collapsed" @on-coll-change="handleCollapsedChange">
          <user :user-avator="userAvator"/>
<!--          <fullscreen v-model="isFullscreen" style="margin-right: 10px;"/>-->
        </header-bar>
      </Header>
      <Content class="main-content-con">
        <Layout class="main-layout-con">
          <Content class="content-wrapper" style="position: relative">
            <div class="left" v-if="canGoBack" @click="goBack">
              <img src="../../assets/images/goback.png" alt="">
            </div>
            <router-view :key="$route.fullPath"/>
          </Content>
        </Layout>
      </Content>
    </Layout>
  </Layout>
</template>
<script>
import HeaderBar from './components/header-bar'
import User from './components/user'
import Fullscreen from './components/fullscreen'
import Language from './components/language'
import { mapMutations } from 'vuex'
import minLogo from '@/assets/images/logo-min.png'
import maxLogo from '@/assets/images/logo.png'
import './main.less'
export default {
  name: 'Main',
  components: {
    HeaderBar,
    Language,
    Fullscreen,
    User
  },
  data () {
    return {
      collapsed: false,
      minLogo,
      maxLogo,
      isFullscreen: false
    }
  },
  computed: {
    userAvator () {
      return this.$store.state.user.avatorImgPath
    },
    menuList () {
      return this.$store.getters.menuList
    },
    local () {
      return this.$store.state.app.local
    },
    canGoBack () {
      return this.$route.name !== 'home'
    }
  },
  methods: {
    ...mapMutations([
      'setBreadCrumb',
    ]),

    goBack () {
      this.$router.go(-1)
    },

    turnToPage (name) {
      if (name.indexOf('isTurnByHref_') > -1) {
        window.open(name.split('_')[1])
        return
      }
      this.$router.push({
        name: name
      })
    },
    handleCollapsedChange (state) {
      this.collapsed = state
    }
  },
  watch: {
    '$route' (newRoute) {
      this.setBreadCrumb(newRoute.matched)
    }
  },
  mounted () {
    /**
     * @description 初始化设置面包屑导航
     */
    this.setBreadCrumb(this.$route.matched)
  }
}
</script>

<style lang="less" scoped>
  .header-con {
    padding: 0;

    /deep/ .header-bar {
      //box-shadow: 0 2px 1px 1px rgba(100,100,100,.1);
      padding: 0 18px;
    }
  }

  .left {
    position: absolute;
    left: 0;
    top: 0;
    width: 18%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;

    img {
      width: 60px;
      height: 60px;
      cursor: pointer;
    }
  }
</style>
