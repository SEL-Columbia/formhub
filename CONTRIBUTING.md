# Contributing

This project adopts the following guidelines:

* [Git flow][]
* [necolas/issue-guidelines][]
* Tim Pope's [Git commit message model][tpope]

[Git flow]: http://nvie.com/posts/a-successful-git-branching-model/
[necolas/issue-guidelines]: https://github.com/necolas/issue-guidelines/blob/master/CONTRIBUTING.md
[tpope]: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html

Spotted an bug or found something you can't otherwise fix? No worries! File an
[issue](#issues).

Fixed a bug, done some refactoring or wrote a new feature? Awesome! File a
[pull request](#pull-requests).

## Issues

1. Search the [GitHub issue tracker][] to see if the issue has already been
   reported

2. Update your local `develop` to check if the issue has already been fixed

Otherwise, confirm the issue is reproducible, create a [reduced test
case][] and file a [new issue][] with as much detail as possible.

[GitHub issue tracker]: https://github.com/eHealthAfrica/LMIS-Chrome/search?type=Issues
[reduced test case]: http://css-tricks.com/reduced-test-cases
[new issue]: https://github.com/eHealthAfrica/LMIS-Chrome/issues/new

## Pull requests

We use the [Git flow][] branching strategy, [hub][] and [git-extras][]. The
following command line examples assume you do too (if not, the basic steps are
the same)

1. Clone and fork the project

    ```bash
    git clone eHealthAfrica/formhub
    cd formhub
    git fork
    ```

2. Create a topic (bug/feature/refactor) branch off `develop`:

    ```bash
    git checkout --track origin/develop
    git feature my-feature
    ```

3. Write and commit some code

    * Group logical steps (Git's interactive rebase can help)
    * Make sure to maintain the project's coding style
        * Our supplied [EditorConfig][] and [JSHint][] settings make it easy!
    * **Write an appropriate test case**
    * Write a short (50 chars or less) commit summary and a detailed body

4. When your topic is finished, make sure it's up-to-date

    ```bash
    git pull --rebase origin develop
    ```

5. Push it to your fork

    ```bash
    git push feature/my-feature [fork-remote]
    ```

6. File a pull request

    ```bash
    git pull-request
    ```

A member of [the team][] will review the request and merge it into `develop` if
it looks good and/or discuss with you accordingly.

[the repo]: https://github.com/eHealthAfrica/formhub
[hub]: http://hub.github.com
[git-extras]: https://github.com/visionmedia/git-extras
[the team]: https://github.com/orgs/eHealthAfrica/teams/ehealth-africa
[JSHint]: http://www.jshint.com/about/
[EditorConfig]: http://editorconfig.org
