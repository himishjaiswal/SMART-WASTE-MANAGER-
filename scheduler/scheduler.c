#include <stdio.h>
#include <string.h>

int n;
int id[100], at[100], bt[100], pr[100];   // id, arrival, burst, priority
int st[100], ct[100];                      // start time, completion time
int done[100], rem[100];

void fcfs() {
    int i, k, t = 0, f;
    for (i = 0; i < n; i++) done[i] = 0;

    for (k = 0; k < n; k++) {
        f = -1;
        // pick the request which came first
        for (i = 0; i < n; i++) {
            if (done[i] == 0) {
                if (f == -1 || at[i] < at[f]) f = i;
            }
        }
        // if vehicle is free but request not came, wait
        if (t < at[f]) t = at[f];

        st[f] = t;
        t = t + bt[f];
        ct[f] = t;
        done[f] = 1;
    }
}

void sjf() {
    int i, k, t = 0, s;
    for (i = 0; i < n; i++) done[i] = 0;

    for (k = 0; k < n; k++) {
        s = -1;
        // among arrived requests, take the smallest burst
        for (i = 0; i < n; i++) {
            if (done[i] == 0 && at[i] <= t) {
                if (s == -1 || bt[i] < bt[s]) s = i;
            }
        }
        // nobody arrived, move time to the next arrival
        if (s == -1) {
            for (i = 0; i < n; i++) {
                if (done[i] == 0) {
                    if (s == -1 || at[i] < at[s]) s = i;
                }
            }
            t = at[s];
        }

        st[s] = t;
        t = t + bt[s];
        ct[s] = t;
        done[s] = 1;
    }
}

void priority() {
    int i, k, t = 0, u;
    for (i = 0; i < n; i++) done[i] = 0;

    for (k = 0; k < n; k++) {
        u = -1;
        // among arrived requests, take the smallest priority number
        for (i = 0; i < n; i++) {
            if (done[i] == 0 && at[i] <= t) {
                if (u == -1 || pr[i] < pr[u]) u = i;
            }
        }
        // nobody arrived, move time to the next arrival
        if (u == -1) {
            for (i = 0; i < n; i++) {
                if (done[i] == 0) {
                    if (u == -1 || at[i] < at[u]) u = i;
                }
            }
            t = at[u];
        }

        st[u] = t;
        t = t + bt[u];
        ct[u] = t;
        done[u] = 1;
    }
}

int q[1000];
int front = 0, rear = 0;
int inq[100];

// put the arrived requests in the queue
void add_to_queue(int t) {
    int i;
    for (i = 0; i < n; i++) {
        if (inq[i] == 0 && at[i] <= t) {
            q[rear] = i;
            rear++;
            inq[i] = 1;
        }
    }
}

void rr(int tq) {
    int i, t = 0, finished = 0, c, run;

    for (i = 0; i < n; i++) {
        rem[i] = bt[i];
        st[i] = -1;
        inq[i] = 0;
    }

    while (finished < n) {
        add_to_queue(t);

        if (front == rear) {   // queue is empty
            t++;
            continue;
        }

        c = q[front];
        front++;

        if (st[c] == -1) st[c] = t;

        run = tq;
        if (rem[c] < tq) run = rem[c];

        t = t + run;
        rem[c] = rem[c] - run;

        add_to_queue(t);       // new requests come before c goes back

        if (rem[c] > 0) {
            q[rear] = c;
            rear++;
        } else {
            ct[c] = t;
            finished++;
        }
    }
}

int main() {
    char algo[20];
    int tq, i, tat, wt;

    scanf("%s", algo);
    scanf("%d", &tq);
    scanf("%d", &n);
    for (i = 0; i < n; i++) {
        scanf("%d %d %d %d", &id[i], &at[i], &bt[i], &pr[i]);
    }

    if (strcmp(algo, "FCFS") == 0) fcfs();
    else if (strcmp(algo, "SJF") == 0) sjf();
    else if (strcmp(algo, "PRIORITY") == 0) priority();
    else if (strcmp(algo, "RR") == 0) rr(tq);
    else {
        printf("Unknown algorithm\n");
        return 1;
    }

    // print: id start completion waiting turnaround
    for (i = 0; i < n; i++) {
        tat = ct[i] - at[i];
        wt = tat - bt[i];
        printf("%d %d %d %d %d\n", id[i], st[i], ct[i], wt, tat);
    }
    return 0;
}