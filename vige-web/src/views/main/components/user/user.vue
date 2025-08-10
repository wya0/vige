<template>
  <div>
    <div class="user-avator-dropdown">
      <Dropdown @on-click="handleClick" trigger="click">
        <a href="javascript:void(0)">
          <span>{{ name }}</span>
<!--          <Icon :size="18" type="md-arrow-dropdown"></Icon>-->
          <Avatar :src="userAvatar" icon="ios-person"/>
        </a>
        <DropdownMenu slot="list">
          <DropdownItem name="logout" divided>退出登录</DropdownItem>
        </DropdownMenu>
      </Dropdown>
    </div>
  </div>
</template>

<script>
  import './user.less'
  import BaseModal from '@/components/modal/base-modal'
  import { get } from 'lodash'

  export default {
    name: 'User',

    components: {
      BaseModal
    },

    computed: {
      name () {
        let username = this.$store.getters['user/username']
        let nickname = this.$store.getters['user/nickname']
        return nickname || username || ''
      }
    },

    data () {
      return {
        loggedOut: false,
        loading: false,
        modal: {
          visible: false,
          title: null,
          onOk: () => {
          },
          onCancel: () => {
          }
        },
      }
    },

    props: {
      userAvatar: {
        type: String,
        default: ''
      }
    },

    methods: {
      logout () {
        this.loggedOut = true
        this.$store.dispatch('logout', {vue: this, makeRequest: true})
      },

      handleClick (name) {
        switch (name) {
          case 'logout':
            this.logout()
            break
        }
      },

    },

    mounted () {
      this.$auth.ready(function () {
        if (this.$auth.check()) {
          this.$store.dispatch('user/refreshUser')
        }
      })
    }
  }
</script>
