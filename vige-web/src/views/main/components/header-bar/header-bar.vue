<template>
  <div class="header-bar">
    <div class="left">
      <div class="icon-wrapper" @click="goHome">
        <img class="icon" src="../../../../assets/images/td-logo.png" alt="">
      </div>
      <custom-bread-crumb show-icon
                          class="bread"
                          :list="breadCrumbList"></custom-bread-crumb>
    </div>
    <div class="custom-content-con">
      <slot></slot>
    </div>
  </div>
</template>
<script>
  import siderTrigger from './sider-trigger'
  import customBreadCrumb from './custom-bread-crumb'
  import './header-bar.less'

  export default {
    name: 'HeaderBar',
    components: {
      siderTrigger,
      customBreadCrumb
    },
    props: {
      collapsed: Boolean
    },
    computed: {
      breadCrumbList () {
        return this.$store.state.breadCrumbList
      }
    },
    methods: {
      goHome () {
        this.$router.push('/')
      },

      handleCollpasedChange (state) {
        this.$emit('on-coll-change', state)
      }
    }
  }
</script>

<style lang="less" scoped>
  .left {
    display: flex;
    //background-color: red;
    align-items: center;
    justify-content: flex-start;
    width: 50%;
    height: 100%;
    position: relative;

    .bread {
      //background-color: orange;
      position: absolute;
      top: 0;
      left: ~"calc(18vw - 10px)";
      height: 100%;
    }
  }
  .icon-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    width: 120px;
    cursor: pointer;
  }

  .icon {
    width: 100%;
    height: auto;
    margin: 0 auto;
    object-fit: contain;
  }
</style>