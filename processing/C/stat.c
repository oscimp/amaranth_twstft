#include <stdio.h>
#include <sys/stat.h>
#include <errno.h>
#include <string.h>
#include <time.h>

int main(int argc, char *argv[])
{
    if (argc != 2)
        printf("Unknown file!\n");
    else {
        struct stat info;
        const char *file = argv[1];
        if (stat(file, &info))
            printf("Failed get information abot \"%s\", errno %d (%s)\n",
                    file, errno, strerror(errno));
        else {
            char at[30], mt[30], ct[30];
            strftime(at, 30, "%F %T %z", localtime(&info.st_atime));
            strftime(mt, 30, "%F %T %z", localtime(&info.st_mtime));
            strftime(ct, 30, "%F %T %z", localtime(&info.st_ctime));
//            printf("Information about %s\n"
//                    "inode %u\n"
//                    "owner %u\n"
//                    "group %u\n"
//                    "size %u\n"
//                    "last access %s\n"
//                    "last modification %s\n"
//                    "last change %s\n",
//                    file,
//                    info.st_ino,
//                    info.st_uid,
//                    info.st_gid,
//                    info.st_size,
 printf("%s\n%s\n%s\n"  ,at,
                    mt,
                    ct);
        }
    }

    return 0;

}
