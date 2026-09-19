# PUBLISH PLAN

Execute only after Terrynce's explicit publish decision. Do NOT run these
from the qualification work order.

1. Create the public GitHub repo: `terryncew/openline-kill-switch`
   (private until the candidate below is pushed).

2. Push the frozen publication candidate: the release-seal commit of
   `~/workspace/openline-kill-switch/` (see REPRODUCIBILITY.md for the
   exact commit SHA). No additional changes on push.

3. Create a release/tag (e.g. `v0.1.0`) if the evidence package merits
   one, pointing at the pushed seal commit.

4. Perform one clean reproduction from the GitHub-hosted repo: fresh
   clone to a new directory, `./RUN.sh`, `./VERIFY.sh`, confirm 7/7
   STOPPED and byte-identical main evidence bundle. Record the result.

5. Publish the approved launch post (copy in THREADS.txt /
   HACKER_NEWS.txt — prepared, not published; final wording is Terrynce's).

Nothing in this plan has been executed. No repo created, nothing pushed,
no tag, no posts.
