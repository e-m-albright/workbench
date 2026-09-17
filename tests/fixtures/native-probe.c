/* Synthetic boundary probe. Never prints process arguments or credential data. */
#include <mach/mach.h>
#include <servers/bootstrap.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/sysctl.h>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    int failures = 0;
    const char *names[] = {
        "com.apple.securityd.xpc",
        "com.apple.SecurityServer",
        "com.apple.coreservices.launchservicesd",
        "com.apple.coreservices.appleevents"
    };
    for (unsigned i = 0; i < sizeof(names) / sizeof(names[0]); i++) {
        mach_port_t service = MACH_PORT_NULL;
        kern_return_t result = bootstrap_look_up(bootstrap_port, names[i], &service);
        failures += result == KERN_SUCCESS;
        if (service != MACH_PORT_NULL) mach_port_deallocate(mach_task_self(), service);
    }
    int pid = atoi(argv[1]);
    int query[] = {CTL_KERN, KERN_PROCARGS2, pid};
    char buffer[262144];
    size_t size = sizeof(buffer);
    failures += sysctl(query, 3, buffer, &size, NULL, 0) == 0;
    failures += kill(pid, 0) == 0;
    printf("%s: host service and process boundary\n", failures ? "FAIL" : "PASS");
    return failures ? 1 : 0;
}
