# Global Rules

## Python Environment Policy

- 所有临时/小型 Python 项目，**必须**用 uv 管理依赖与虚拟环境。
- **禁止**直接用 pip、pip3、poetry、conda 等在宿主环境安装包。
- 任何 Python 代码，都要在 uv 创建的虚拟环境中运行。

## Java Environment Policy

- Java JDK 和 Maven/Gradle **必须**通过 SDKMAN! 管理。
- **禁止**通过 brew install java/maven 全局安装 JDK 或构建工具。
- 多版本 JDK 通过 `sdk install java <version>` 安装，`sdk use` 切换。
- 项目级 JDK 版本通过 `sdk use` 在项目目录设置。

## 铁律

- 只要你写 Python，默认就用 uv；没问我就自己按上面规则建环境。
- 不允许把包装到系统/全局 Python 里。
- 只要你写 Java，默认就用 SDKMAN! 管理的 JDK 和 Maven；没问我就自己按上面规则安装。
- 不允许通过 brew 或系统包管理器全局安装 JDK/Maven。
