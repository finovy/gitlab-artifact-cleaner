# Gitlab Artifacts Cleaner

一个用于清理Gitlab Artifacts的小工具

A small tool for cleaning Gitlab Artifacts

### How to use this image

```
docker dun finovy/gitlab-artifact-cleaner
```

### Environment Variables

#### `BASE_URL`

The URL address of gitlab, for example https://git.finovy.cn/

#### `ACCESS_TOKEN`

gitlab Personal access tokens, Reference documents https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html

#### `GROUP`

Gitlab group names that need to be cleaned

#### `EXPIRES`

How many days ago did you clean up artifacts, default to 3
