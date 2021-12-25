(use-modules
 ((guix licenses) #:prefix license:)
 (gnu packages glib)
 (gnu packages gnome)
 (gnu packages man)
 (gnu packages python)
 (guix build-system gnu)
 (guix download)
 (guix gexp)
 (guix git-download)
 (guix packages)
 (ice-9 popen)
 (ice-9 rdelim)
 )

(define-public picmover
  (package
    (name "picmover")
    (version "1.2.5")
    (source
     (origin
     (method git-fetch)
     (uri (git-reference
           (url "https://github.com/plattfot/picmover")
           (commit (string-append "v" version))))
     (sha256
      (base32
       "1js9zlg2hzarkqwiadkmj7kk7dxvij2yjwlrf6xdbsa3ckym55yz"))
     (file-name (git-file-name name version))))
    (build-system gnu-build-system)
    (arguments
     '(#:tests? #f
       #:make-flags (list (string-append "DESTDIR=" (assoc-ref %outputs "out")))
       #:phases (modify-phases %standard-phases
                  (delete 'configure))))
    (native-inputs `())
    (inputs `(("python" ,python-wrapper)
              ("man-db" ,man-db)))
    (propagated-inputs `(("python-pygobject" ,python-pygobject)
                         ("gexiv2" ,gexiv2)
                         ("libnotify" ,libnotify)))
    (synopsis "Image and video importer/organizer")
    (description
     "Moving pictures and videos from one location to another, using
metadata to determine camera maker, model, date and location. Useful
for importing files from a camera.")
    (home-page "https://github.com/plattfot/picmover")
    (license license:gpl3+)))

;; From the talk "Just build it with Guix" by Efraim Flashner
;; presented on the Guix days 2020
;; https://guix.gnu.org/en/blog/2020/online-guix-day-announce-2/
(define %source-dir (dirname (current-filename)))

(define %git-commit
  (read-string (open-pipe "git show HEAD | head -1 | cut -d ' ' -f2" OPEN_READ)))

(define (skip-git-and-build-directory file stat)
  "Skip the `.git` and `build` directory when collecting the sources."
  (let ((name (basename file)))
    (not (or (string=? name ".git") (string=? name "build")))))

(package
  (inherit picmover)
  (name "picmover-git")
  (version (git-version (package-version picmover) "HEAD" %git-commit))
  (source (local-file %source-dir
                      #:recursive? #t
                      #:select? skip-git-and-build-directory)))
