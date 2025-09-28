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