import {
  AlertTriangle,
  Clock3,
  Search,
  X,
} from "lucide-react";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import { getEvents } from "../services/api";

type SearchEvent = {
  id: number;
  title: string;
  source?: string;
  event_type?: string;
  severity?: string;
  status?: string;
  graph_id?: string;
};

type GlobalSearchProps = {
  activeEventId: number | undefined;
  onSelectEvent: (
    event: SearchEvent
  ) => void;
};

function normalizeEvents(
  result: any
): SearchEvent[] {
  const data =
    result?.data ??
    result;

  let items: any[] = [];

  if (Array.isArray(data)) {
    items = data;
  } else if (
    Array.isArray(
      data?.events
    )
  ) {
    items = data.events;
  } else if (
    Array.isArray(
      data?.items
    )
  ) {
    items = data.items;
  }

  return items
    .map(
      (event: any) => {
        const id = Number(
          event?.id ??
            event?.event_id ??
            0
        );

        return {
          id,

          title: String(
            event?.title ??
              event?.name ??
              "Untitled event"
          ),

          source:
            event?.source ??
            "AtmoGraph",

          event_type:
            event?.event_type ??
            event?.type ??
            "unknown",

          severity:
            event?.severity ??
            "medium",

          status:
            event?.status ??
            "active",

          graph_id:
            event?.graph_id ??
            `event_${id}`,
        };
      }
    )
    .filter(
      (event) =>
        Number.isFinite(
          event.id
        ) &&
        event.id > 0
    );
}

function severityClass(
  severity?: string
) {
  switch (
    severity?.toLowerCase()
  ) {
    case "critical":
      return "critical";

    case "high":
      return "high";

    case "low":
      return "low";

    default:
      return "medium";
  }
}

export default function GlobalSearch({
  activeEventId,
  onSelectEvent,
}: GlobalSearchProps) {
  const [
    query,
    setQuery,
  ] = useState("");

  const [
    results,
    setResults,
  ] = useState<SearchEvent[]>(
    []
  );

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    open,
    setOpen,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const containerRef =
    useRef<HTMLDivElement>(
      null
    );

  /*
   * ==========================================================
   * CLOSE WHEN CLICKING OUTSIDE
   * ==========================================================
   */

  useEffect(() => {
    function handleOutsideClick(
      event: MouseEvent
    ) {
      if (
        containerRef.current &&
        !containerRef.current.contains(
          event.target as Node
        )
      ) {
        setOpen(false);
      }
    }

    document.addEventListener(
      "mousedown",
      handleOutsideClick
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleOutsideClick
      );
    };
  }, []);

  /*
   * ==========================================================
   * KEYBOARD SHORTCUT
   * ==========================================================
   */

  useEffect(() => {
    function handleKeyboard(
      event: KeyboardEvent
    ) {
      const target =
        event.target as HTMLElement;

      const isTyping =
        target?.tagName ===
          "INPUT" ||
        target?.tagName ===
          "TEXTAREA" ||
        target?.isContentEditable;

      if (
        event.key === "/" &&
        !isTyping
      ) {
        event.preventDefault();

        const input =
          containerRef.current?.querySelector(
            "input"
          ) as HTMLInputElement | null;

        input?.focus();

        setOpen(true);
      }

      if (
        event.key === "Escape"
      ) {
        setOpen(false);
      }
    }

    document.addEventListener(
      "keydown",
      handleKeyboard
    );

    return () => {
      document.removeEventListener(
        "keydown",
        handleKeyboard
      );
    };
  }, []);

  /*
   * ==========================================================
   * SEARCH
   * ==========================================================
   */

  useEffect(() => {
    const trimmedQuery =
      query.trim();

    if (!trimmedQuery) {
      setResults([]);
      setError("");
      setLoading(false);

      return;
    }

    let cancelled = false;

    const timer =
      window.setTimeout(
        async () => {
          try {
            setLoading(true);
            setError("");

            const result =
              await getEvents(
                trimmedQuery,
                "",
                "",
                12
              );

            if (!cancelled) {
              setResults(
                normalizeEvents(
                  result
                )
              );
            }
          } catch (
            exception
          ) {
            if (!cancelled) {
              console.error(
                "Global search failed:",
                exception
              );

              setResults([]);

              setError(
                exception instanceof
                  Error
                  ? exception.message
                  : "Search failed."
              );
            }
          } finally {
            if (!cancelled) {
              setLoading(false);
            }
          }
        },
        280
      );

    return () => {
      window.clearTimeout(
        timer
      );
    };
  }, [query]);

  /*
   * ==========================================================
   * EVENT SELECTION
   * ==========================================================
   */

  function selectEvent(
    event: SearchEvent
  ) {
    onSelectEvent(event);

    setQuery("");
    setResults([]);
    setError("");
    setOpen(false);
  }

  function clearSearch() {
    setQuery("");
    setResults([]);
    setError("");
    setOpen(false);
  }

  return (
    <div
      className="global-search"
      ref={containerRef}
    >

      {/* SEARCH INPUT */}

      <div className="search-box">

        <Search size={17} />

        <input
          type="text"
          value={query}
          onFocus={() =>
            setOpen(true)
          }
          onChange={(event) => {
            setQuery(
              event.target.value
            );

            setOpen(true);
          }}
          onKeyDown={(event) => {
            if (
              event.key ===
              "Escape"
            ) {
              clearSearch();
            }
          }}
          placeholder="Search events, suppliers..."
          aria-label="Search AtmoGraph"
          autoComplete="off"
        />

        {query ? (
          <button
            type="button"
            className="search-clear"
            onClick={
              clearSearch
            }
            aria-label="Clear search"
          >
            <X size={14} />
          </button>
        ) : (
          <span className="search-shortcut">
            /
          </span>
        )}

      </div>


      {/* SEARCH DROPDOWN */}

      {open &&
        query.trim() && (
          <div className="global-search-dropdown">

            <div className="global-search-header">

              <span>
                INTELLIGENCE SEARCH
              </span>

              {loading && (
                <span>
                  Searching...
                </span>
              )}

            </div>


            {/* ERROR */}

            {error && (
              <div className="global-search-empty">

                <AlertTriangle
                  size={15}
                />

                <span>
                  {error}
                </span>

              </div>
            )}


            {/* NO RESULTS */}

            {!loading &&
              !error &&
              results.length ===
                0 && (
                <div className="global-search-empty">

                  <Search
                    size={15}
                  />

                  <span>
                    No matching events found.
                  </span>

                </div>
              )}


            {/* RESULTS */}

            {results.length >
              0 && (
              <div className="global-search-results">

                {results.map(
                  (event) => {

                    const isCurrent =
                      event.id ===
                      activeEventId;

                    return (
                      <button
                        type="button"
                        key={
                          event.id
                        }
                        className={`global-search-result ${
                          isCurrent
                            ? "current"
                            : ""
                        }`}
                        onClick={() =>
                          selectEvent(
                            event
                          )
                        }
                      >

                        <div className="global-search-result-icon">

                          <AlertTriangle
                            size={15}
                          />

                        </div>


                        <div className="global-search-result-content">

                          <strong>
                            {event.title}
                          </strong>

                          <span>
                            Event #
                            {event.id}
                            {" · "}
                            {event.event_type}
                            {" · "}
                            {event.source}
                          </span>

                        </div>


                        <div className="global-search-result-right">

                          <span
                            className={`source-severity ${severityClass(
                              event.severity
                            )}`}
                          >
                            {(
                              event.severity ??
                              "medium"
                            ).toUpperCase()}
                          </span>


                          {isCurrent && (
                            <span className="current-event-label">
                              CURRENT
                            </span>
                          )}

                        </div>

                      </button>
                    );
                  }
                )}

              </div>
            )}


            {/* FOOTER */}

            {!loading &&
              !error &&
              results.length >
                0 && (
                <div className="global-search-footer">

                  <Clock3
                    size={12}
                  />

                  <span>
                    Select an event to update
                    the active intelligence case.
                  </span>

                </div>
              )}

          </div>
        )}

    </div>
  );
}