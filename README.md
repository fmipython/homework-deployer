# homework-deployer

A small script that deploys homeworks for the Python course, from the private repo to the public one.

## Functionality

A deployment event is when the required files get picked up from private repo, and put into the public one.
The event has files to transfer, origin repo, destination repo and a date. Also a name/id.

Users of the script can schedule such events by using `at` and configuration files.

The script will take care of the scheduling, execution, access and everything else.

Detailed functionalities:

- Register a deployment event.
- List all deployment events.
- Deregister a deployment event.
- Manually run a deployment event.
- Execute deployment events.
- Pull files from a (private) repository.
- Push files to a repository.
- Run CI/CD actions (this is more of a wish).

## Config files

### Patterns supported

#### Source pattern

- File - Copy single file
- Directory - Copy entier directory
- Glob - Copy files and directories matching the pattern

#### Destination pattern

- None - Keep the original structure
- File - Copy the file to the given name
- Directory - Copy the contents to the given directory

Example:
If `A` and `B` are the root of the repositories.

||None|File (`d/g.txt`)|Directory (`B/h`)|
|----|----|----|----|
|**File** (`A/c/e.txt`)|`B/c/e.txt`|`B/d/e.txt`|`B/h/e.txt`|
|**Directory** (`A/c`)|`B/c`|Error|`B/h`|
|**Glob** (`A/c/*.py`)|`B/c/*.py`|Error|`B/h/*.py`|

*Note - no need to pass the repo path in the patterns part.*
